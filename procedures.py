from typing import Any, final, Optional
from abc import abstractmethod
from tools import Status, status, StatusMeta


# Basic calculation logic unit
# CONTAINS:
#   - input slots (names and types)
#   - output slots (names and types)
#   - input values
#   - output values
#   - input status (changed after last run or not)
class Procedure(Status):
    
    # COMMANDS

    # Set input value
    # PRE: `slot` is valid input slot name
    # PRE: type of `value` is compatible with slot
    # PRE: `value` is acceptable for the procedure
    # POST: input value in slot `slot` is set to `value`
    @abstractmethod
    @status("OK", "INVALID_SLOT", "INVALID_TYPE", "INVALID_VALUE")
    def put(self, slot: str, value: Any) -> None:
        assert False

    # Run procedure
    # PRE: procedure can run successfully with current inputs
    # POST: output values are set
    # POST: input values status set to unchanged
    @abstractmethod
    @status("OK", "INVALID_INPUT", "RUN_FAILED")
    def run(self) -> None:
        assert False


    # QUERIES

    # Get description of input slots
    @abstractmethod
    def get_input_slots(self) -> dict[str, type]:
        assert False

    # Get description of output slots
    @abstractmethod
    def get_output_slots(self) -> dict[str, type]:
        assert False

    # Check if the procedure needs run to update outputs
    @abstractmethod
    def needs_run(self) -> bool:
        assert False

    # Get output value
    # PRE: slot is valid output slot name
    # PRE: run was successful after last input change
    @abstractmethod
    @status("OK", "INVALID_SLOT", "NEEDS_RUN")
    def get(self, slot: str) -> Any:
        assert False


class CalculatorMeta(StatusMeta):
    def __new__(cls, class_name: str, bases: tuple[type, ...],
            namespace: dict[str, Any], **kwargs: Any) -> type:
        input_slots, input_names = cls._get_fields(class_name, namespace, "INPUTS")
        output_slots, output_names = cls._get_fields(class_name, namespace, "OUTPUTS")
        namespace["__input_slots"] = input_slots
        namespace["__output_slots"] = output_slots
        namespace["__input_names"] = input_names
        namespace["__output_names"] = output_names
        return super().__new__(cls, class_name, bases, namespace, **kwargs)

    @staticmethod
    def _get_fields(class_name: str, namespace: dict[str, Any], key: str
            ) -> tuple[dict[str, type], dict[str, str]]:
        if "__annotations__" not in namespace or key not in namespace:
            return dict[str, type](), dict[str, str]()
        annotations = namespace["__annotations__"]
        types = dict[str, type]()
        names = dict[str, str]()
        for slot in namespace[key]:
            if slot in annotations:
                types[slot] = annotations[slot]
                names[slot] = slot
                continue
            protected_field = f"_{slot}"
            if protected_field in annotations:
                types[slot] = annotations[protected_field]
                names[slot] = protected_field
                continue
            private_field = f"_{class_name}__{slot}"
            if private_field in annotations:
                types[slot] = annotations[private_field]
                names[slot] = private_field
                continue
        return types, names


# Procedure that calculates outputs using custom algorithm
class Calculator(Procedure, metaclass=CalculatorMeta):

    __missing_inputs: set[str]
    __needs_run: bool
    
    def __get_input_slots(self) -> dict[str, type]:
        return getattr(self, "__input_slots")

    def __get_output_slots(self) -> dict[str, type]:
        return getattr(self, "__output_slots")

    def __set(self, slot: str, value: Any) -> None:
        setattr(self, getattr(self, "__input_names")[slot], value)

    def __get(self, slot: str) -> Any:
        return getattr(self, getattr(self, "__output_names")[slot])

    
    # CONSTRUCTOR
    def __init__(self) -> None:
        super().__init__()
        self.__missing_inputs = set(self.__get_input_slots().keys())
        self.__needs_run = True


    # COMMANDS

    # Set input value
    # PRE: `slot` is valid input slot name
    # PRE: type of `value` is compatible with slot
    # PRE: `value` is acceptable for the procedure
    # POST: input value in slot `slot` is set to `value`
    @final
    @status("OK", "INVALID_SLOT", "INVALID_TYPE", "INVALID_VALUE")
    def put(self, slot: str, value: Any) -> None:
        input_slots = self.__get_input_slots()
        if slot not in input_slots:
            self._set_status("put", "INVALID_SLOT")
            return
        if not _type_fits(type(value), input_slots[slot]):
            self._set_status("put", "INVALID_TYPE")
            return
        if not self._is_valid_value(slot, value):
            self._set_status("put", "INVALID_VALUE")
            return
        self.__set(slot, value)
        if slot in self.__missing_inputs:
            self.__missing_inputs.remove(slot)
        self.__needs_run = True
        self._set_status("put", "OK")

    # Run procedure
    # PRE: procedure can run successfully with current inputs
    # POST: output values are set
    # POST: input values status set to unchanged
    @final
    @status("OK", "INVALID_INPUT", "RUN_FAILED")
    def run(self) -> None:
        if len(self.__missing_inputs) > 0:
            self._set_status("run", "INVALID_INPUT")
            return
        self.calculate()
        if not self.is_status("calculate", "OK"):
            self._set_status("run", "RUN_FAILED")
            return
        self.__needs_run = False
        self._set_status("run", "OK")

    # Calculate the outputs
    # Used by `run` method
    # PRE: procedure can run successfully with current inputs
    @abstractmethod
    @status("OK", "ERROR")
    def calculate(self) -> None:
        assert False


    # QUERIES

    # Get description of input slots
    def get_input_slots(self) -> dict[str, type]:
        return self.__get_input_slots()

    # Get description of output slots
    def get_output_slots(self) -> dict[str, type]:
        return self.__get_output_slots()

    # Check if the procedure needs run to update outputs
    def needs_run(self) -> bool:
        return self.__needs_run

    # Get output value
    # PRE: slot is valid output slot name
    # PRE: run was successful after last input change
    @status("OK", "INVALID_SLOT", "NEEDS_RUN")
    def get(self, slot: str) -> Any:
        output_slots = self.__get_output_slots()
        if slot not in output_slots:
            self._set_status("get", "INVALID_SLOT")
            return
        if self.needs_run():
            self._set_status("get", "NEEDS_RUN")
            return
        self._set_status("get", "OK")
        return self.__get(slot)

    # Check input value
    def _is_valid_value(self, slot: str, value: Any) -> bool:
        assert False


# Data node for Composition
# CONTAINS:
#   - type
#   - status (valid or not)
#   - data (if valid)
#   - input procedure node (optional)
#   - output procedure nodes
@final
class DataNode(Status):

    __type: type
    __is_valid: bool
    __data: Any
    __input: Optional["ProcNode"]
    __outputs: set["ProcNode"]
    
    # CONSTRUCTOR
    # POST: type is `data_type`
    # POST: data is invalid
    # POST: no inputs
    # POST: no outputs
    def __init__(self, data_type: type) -> None:
        super().__init__()
        self.__type = data_type
        self.__is_valid = False
        self.__input = None
        self.__outputs = set()


    # COMMANDS

    # Add input procedure node
    # PRE: `input` is not in input or outputs
    # PRE: input is empty
    # POST: input is `input`
    @status("OK", "ALREADY_LINKED", "MULTIPLE_INPUTS")
    def add_input(self, input: "ProcNode") -> None:
        if input is self.__input or input in self.__outputs:
            self._set_status("add_input", "ALREADY_LINKED")
            return
        if self.__input is not None:
            self._set_status("add_input", "MULTIPLE_INPUTS")
            return
        self.__input = input
        self._set_status("add_input", "OK")

    # Add output procedure node
    # PRE: `output` is not in input or outputs
    # POST: `output` is in outputs
    @status("OK", "ALREADY_LINKED")
    def add_output(self, output: "ProcNode") -> None:
        if output is self.__input or output in self.__outputs:
            self._set_status("add_output", "ALREADY_LINKED")
            return
        self.__outputs.add(output)
        self._set_status("add_output", "OK")

    # Mark node as invalid
    # POST: data is invalid
    def invalidate(self) -> None:
        self.__is_valid = False

    # Set data
    # PRE: `value` type fits data type
    # POST: data is valid
    # POST: data is `value`
    @status("OK", "INVALID_TYPE")
    def put(self, value: Any) -> None:
        if not _type_fits(type(value), self.__type):
            self._set_status("put", "INVALID_TYPE")
            return
        self.__is_valid = True
        self.__data = value
        self._set_status("put", "OK")


    # QUERIES

    # Get input
    def get_input(self) -> Optional["ProcNode"]:
        return self.__input

    # Get outputs
    def get_outputs(self) -> set["ProcNode"]:
        return self.__outputs.copy()

    # Get data type
    def get_type(self) -> type:
        return self.__type

    # Check wether data is valid
    def is_valid(self) -> bool:
        return self.__is_valid

    # Get data
    # PRE: data is valid
    @status("OK", "INVALID_DATA")
    def get(self) -> Any:
        if not self.is_valid():
            self._set_status("get", "INVALID_DATA")
            return None
        self._set_status("get", "OK")
        return self.__data


# Procedure node for Composition
# CONTAINS:
#   - procedure
#   - status (needs run or not)
#   - named input data nodes
#   - named output data nodes
@final
class ProcNode(Status):

    __proc: Procedure
    __needs_run: bool
    __inputs: dict[str, DataNode]
    __outputs: dict[str, DataNode]

    # CONSTRUCTOR
    # POST: procedure is `proc`
    # POST: needs run
    def __init__(self, proc: Procedure) -> None:
        super().__init__()
        self.__proc = proc
        self.__needs_run = True
        self.__inputs = dict()
        self.__outputs = dict()


    # COMMANDS

    # Add input data node
    # PRE: `slot` is correct input slot
    # PRE: `input` is not in outputs
    # PRE: `input` type fits procedure input at `slot`
    # POST: `input` is in inputs at `slot`
    @status("OK", "INVALID_SLOT", "SLOT_OCCUPIED", "ALREADY_LINKED", "INVALID_TYPE")
    def add_input(self, slot: str, input: DataNode) -> None:
        if slot not in self.__proc.get_input_slots():
            self._set_status("add_input", "INVALID_SLOT")
            return
        if slot in self.__inputs:
            self._set_status("add_input", "SLOT_OCCUPIED")
            return
        if input in self.__inputs.values() or input in self.__outputs.values():
            self._set_status("add_input", "ALREADY_LINKED")
            return
        if not _type_fits(input.get_type(), self.__proc.get_input_slots()[slot]):
            self._set_status("add_input", "INVALID_TYPE")
            return
        self.__inputs[slot] = input
        self._set_status("add_input", "OK")

    # Add output data node
    # PRE: `slot` is correct output slot
    # PRE: `output` is not in inputs or outputs
    # PRE: `output` type fits procedure output at `slot`
    # POST: `output` is in outputs at `slot` 
    @status("OK", "INVALID_SLOT", "SLOT_OCCUPIED", "ALREADY_LINKED", "INVALID_TYPE")
    def add_output(self, slot: str, output: DataNode) -> None:
        if slot not in self.__proc.get_output_slots():
            self._set_status("add_output", "INVALID_SLOT")
            return
        if slot in self.__outputs:
            self._set_status("add_output", "SLOT_OCCUPIED")
            return
        if output in self.__inputs.values() or output in self.__outputs.values():
            self._set_status("add_output", "ALREADY_LINKED")
            return
        if not _type_fits(output.get_type(), self.__proc.get_output_slots()[slot]):
            self._set_status("add_output", "INVALID_TYPE")
            return
        self.__outputs[slot] = output
        self._set_status("add_output", "OK")

    # Mark that procedure needs run
    # POST: needs run
    def invalidate(self) -> None:
        assert False

    
    # QUERIES

    # Get inputs
    def get_inputs(self) -> dict[str, DataNode]:
        return self.__inputs.copy()

    # Get outputs
    def get_outputs(self) -> dict[str, DataNode]:
        return self.__outputs.copy()

    # Get procedure
    def get_proc(self) -> Procedure:
        return self.__proc

    # Check if procedure needs run
    def needs_run(self) -> bool:
        return self.__needs_run


@final
class Composition(Procedure):

    __input_slots: dict[str, type]
    __output_slots: dict[str, type]
    __input_proc: dict[str, dict[Procedure, str]]
    __output_proc: dict[str, tuple[Procedure, str]]
    __proc_input: dict[Procedure, dict[str, str]]
    __proc_output: dict[Procedure, dict[str, str]]
    __proc_to_run: set[Procedure]

    
    # CONSTRUCTOR
    @status("OK", "ERROR", name="init")
    def __init__(self, contents: list[tuple[Procedure, dict[str, str], dict[str, str]]]) -> None:
        super().__init__()
        self._set_status("init", "OK")
        input_slots = dict[str, type]()
        output_slots = dict[str, type]()
        self.__input_proc = dict()
        self.__output_proc = dict()
        self.__proc_input = dict()
        self.__proc_output = dict()
        self.__proc_to_run = set()
        for proc, proc_inputs, proc_outputs in contents:
            proc_input_slots = proc.get_input_slots()
            proc_output_slots = proc.get_output_slots()
            self.__proc_input[proc] = dict()
            self.__proc_output[proc] = dict()
            self.__proc_to_run.add(proc)
            for slot, name in proc_inputs.items():
                input_slots[name] = proc_input_slots[slot]
                if name not in self.__input_proc:
                    self.__input_proc[name] = dict()
                self.__input_proc[name][proc] = slot
                self.__proc_input[proc][slot] = name
            for slot, name in proc_outputs.items():
                output_slots[name] = proc_output_slots[slot]
                self.__output_proc[name] = (proc, slot)
                self.__proc_output[proc][slot] = name
        for slot in input_slots.keys() & output_slots.keys():
            del input_slots[slot]
            del output_slots[slot]
        self.__input_slots = input_slots
        self.__output_slots = output_slots
    
    
    # COMMANDS

    # Set input value
    # PRE: `slot` is valid input slot name
    # PRE: type of `value` is compatible with slot
    # PRE: `value` is acceptable for the procedure
    # POST: input value in slot `slot` is set to `value`
    @status("OK", "INVALID_SLOT", "INVALID_TYPE", "INVALID_VALUE")
    def put(self, slot: str, value: Any) -> None:
        if slot not in self.__input_slots:
            self._set_status("put", "INVALID_SLOT")
            return
        for proc, input_slot in self.__input_proc[slot].items():
            proc.put(input_slot, value)
            if not proc.is_status("put", "OK"):
                self._set_status("put", proc.get_status("put"))
                return
            self.__invalidate_proc(proc)
        self._set_status("put", "OK")


    # Run procedure
    # PRE: procedure can run successfully with current inputs
    # POST: output values are set
    # POST: input values status set to unchanged
    @status("OK", "INVALID_INPUT", "RUN_FAILED")
    def run(self) -> None:
        for name in self.__output_slots.keys():
            self.__validate_proc(self.__output_proc[name][0])
        assert(not self.needs_run())
        self._set_status("run", "OK")

    
    def __invalidate_proc(self, proc: Procedure):
        if proc in self.__proc_to_run:
            return
        self.__proc_to_run.add(proc)
        for _, name in self.__proc_output[proc].items():
            if name not in self.__input_proc:
                continue
            for other_proc, _ in self.__input_proc[name].items():
                self.__invalidate_proc(other_proc)


    def __validate_proc(self, proc: Procedure):
        if proc not in self.__proc_to_run:
            return
        for _, name in self.__proc_input[proc].items():
            if name not in self.__output_proc:
                continue
            self.__validate_proc(self.__output_proc[name][0])
        proc.run()
        for slot, name in self.__proc_output[proc].items():
            if name not in self.__input_proc:
                continue
            value = proc.get(slot)
            for dest_proc, dest_slot in self.__input_proc[name].items():
                dest_proc.put(dest_slot, value)
        self.__proc_to_run.remove(proc)


    # QUERIES

    # Get description of input slots
    def get_input_slots(self) -> dict[str, type]:
        return self.__input_slots

    # Get description of output slots
    def get_output_slots(self) -> dict[str, type]:
        return self.__output_slots

    # Check if the procedure needs run to update outputs
    def needs_run(self) -> bool:
        return len(self.__proc_to_run) > 0

    # Get output value
    # PRE: slot is valid output slot name
    # PRE: run was successful after last input change
    @status("OK", "INVALID_SLOT", "NEEDS_RUN")
    def get(self, slot: str) -> Any:
        proc, output_slot = self.__output_proc[slot]
        value = proc.get(output_slot)
        self._set_status("get", proc.get_status("get"))
        return value


def _type_fits(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False
