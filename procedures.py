from typing import Any, final
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
    def set(self, slot: str, value: Any) -> None:
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
    def set(self, slot: str, value: Any) -> None:
        input_slots = self.__get_input_slots()
        if slot not in input_slots:
            self._set_status("set", "INVALID_SLOT")
            return
        if not _type_fits(type(value), input_slots[slot]):
            self._set_status("set", "INVALID_TYPE")
            return
        if not self._is_valid_value(slot, value):
            self._set_status("set", "INVALID_VALUE")
            return
        self.__set(slot, value)
        if slot in self.__missing_inputs:
            self.__missing_inputs.remove(slot)
        self.__needs_run = True
        self._set_status("set", "OK")

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


@final
class Composition(Procedure):

    __input_slots: dict[str, type]
    __input_map: dict[str, tuple[Procedure, str]]
    __output_slots: dict[str, type]
    __output_map: dict[str, tuple[Procedure, str]]
    __needs_run: bool

    
    # CONSTRUCTOR
    @status("OK", "ERROR", name="init")
    def __init__(self, contents: list[tuple[Procedure, dict[str, str], dict[str, str]]]) -> None:
        super().__init__()
        self._set_status("init", "OK")
        input_slots = dict[str, type]()
        output_slots = dict[str, type]()
        self.__input_map = dict()
        self.__output_map = dict()
        for proc, proc_inputs, proc_outputs in contents:
            proc_input_slots = proc.get_input_slots()
            proc_output_slots = proc.get_output_slots()
            for slot, name in proc_inputs.items():
                input_slots[name] = proc_input_slots[slot]
                self.__input_map[name] = (proc, slot)
            for slot, name in proc_outputs.items():
                output_slots[name] = proc_output_slots[slot]
                self.__output_map[name] = (proc, slot)
        for slot in input_slots.keys() & output_slots.keys():
            del input_slots[slot]
            del output_slots[slot]
        self.__input_slots = input_slots
        self.__output_slots = output_slots
        self.__needs_run = True
    
    
    # COMMANDS

    # Set input value
    # PRE: `slot` is valid input slot name
    # PRE: type of `value` is compatible with slot
    # PRE: `value` is acceptable for the procedure
    # POST: input value in slot `slot` is set to `value`
    @status("OK", "INVALID_SLOT", "INVALID_TYPE", "INVALID_VALUE")
    def set(self, slot: str, value: Any) -> None:
        if slot not in self.__input_slots:
            self._set_status("set", "INVALID_SLOT")
            return
        proc, input_slot = self.__input_map[slot]
        proc.set(input_slot, value)
        if not proc.is_status("set", "OK"):
            self._set_status("set", proc.get_status("set"))
            return
        self.__needs_run = True
        self._set_status("set", "OK")

    # Run procedure
    # PRE: procedure can run successfully with current inputs
    # POST: output values are set
    # POST: input values status set to unchanged
    @status("OK", "INVALID_INPUT", "RUN_FAILED")
    def run(self) -> None:
        self.__needs_run = False
        self._set_status("run", "OK")


    # QUERIES

    # Get description of input slots
    def get_input_slots(self) -> dict[str, type]:
        return self.__input_slots

    # Get description of output slots
    def get_output_slots(self) -> dict[str, type]:
        return self.__output_slots

    # Check if the procedure needs run to update outputs
    def needs_run(self) -> bool:
        return self.__needs_run

    # Get output value
    # PRE: slot is valid output slot name
    # PRE: run was successful after last input change
    @status("OK", "INVALID_SLOT", "NEEDS_RUN")
    def get(self, slot: str) -> Any:
        proc, output_slot = self.__output_map[slot]
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
