from typing import Any, final, Optional, Generic, TypeVar
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


Input = TypeVar("Input")
Output = TypeVar("Output")


# Generic base node class for Composition
# CONTAINS:
#   - inputs (may be limited to single)
#   - outputs (may be limited to single)
#   - status (valid or not)
class Node(Generic[Input, Output], Status):

    __inputs: set[Input]
    __outputs: set[Output]
    __single_input: bool
    __single_output: bool
    __is_valid: bool


    # CONSTRUCTOR
    # POST: no inputs
    # POST: no outputs
    # POST: node is invalid
    def __init__(self, single_input: bool, single_output: bool) -> None:
        Status.__init__(self)
        self.__inputs = set()
        self.__outputs = set()
        self.__single_input = single_input
        self.__single_output = single_output
        self.__is_valid = False


    # COMMANDS

    # Add input node
    # PRE: `input` is not in inputs or outputs
    # PRE: inputs not full
    # POST: `input` is in inputs
    @status("OK", "ALREADY_LINKED", "TOO_MANY_LINKS")
    def add_input(self, input: Input) -> None:
        if input in self.__inputs or input in self.__outputs:
            self._set_status("add_input", "ALREADY_LINKED")
            return
        if self.__single_input and len(self.__inputs) > 0:
            self._set_status("add_input", "TOO_MANY_LINKS")
            return
        self.__inputs.add(input)
        self._set_status("add_input", "OK")

    # Add output node
    # PRE: `output` is not in input or outputs
    # PRE: outputs not full
    # POST: `output` is in outputs
    @status("OK", "ALREADY_LINKED", "TOO_MANY_LINKS")
    def add_output(self, output: Output) -> None:
        if output in self.__inputs or output in self.__outputs:
            self._set_status("add_output", "ALREADY_LINKED")
            return
        if self.__single_output and len(self.__outputs) > 0:
            self._set_status("add_output", "TOO_MANY_LINKS")
            return
        self.__outputs.add(output)
        self._set_status("add_output", "OK")

    # Mark node as valid
    def validate(self) -> None:
        self.__is_valid = True

    # Mark node as invalid
    def invalidate(self) -> None:
        self.__is_valid = False

    
    # QUERIES

    # Get input
    def get_inputs(self) -> set[Input]:
        return self.__inputs.copy()

    # Get outputs
    def get_outputs(self) -> set[Output]:
        return self.__outputs.copy()

    # Check node status
    def is_valid(self) -> bool:
        return self.__is_valid


# Slot mixin for nodes
# CONTAINS:
#   - slot id
#   - data type
class SlotMixin(Status):

    __slot: str
    __type: type

    # CONSTRUCTOR
    # POST: slot id is `slot`
    # POST: data type is `data_type`
    def __init__(self, slot: str, data_type: type) -> None:
        Status.__init__(self)
        self.__slot = slot
        self.__type = data_type


    # QUERIES

    # Get slot id
    def get_slot(self) -> str:
        return self.__slot

    # Get data type
    def get_type(self) -> type:
        return self.__type


# Input slot node for Composition
# CONTAINS:
#   - up to one input OutputNode
#   - up to one output ProcNode
#   - slot id
#   - data type
class InputNode(Node["OutputNode", "ProcNode"], SlotMixin):

    # CONSTRUCTOR
    # POST: no input
    # POST: no output
    # POST: slot id is `slot`
    # POST: data type is `data_type`
    def __init__(self, slot: str, data_type: type) -> None:
        Node.__init__(self, True, True)
        SlotMixin.__init__(self, slot, data_type)


# Output slot node for Composition
# CONTAINS:
#   - up to one input ProcNode
#   - outputs (InputNode)
#   - slot id
#   - data type
class OutputNode(Node["ProcNode", "InputNode"], SlotMixin):

    # CONSTRUCTOR
    # POST: no input
    # POST: no outputs
    # POST: slot id is `slot`
    # POST: data type is `data_type`
    def __init__(self, slot: str, data_type: type) -> None:
        Node.__init__(self, True, False)
        SlotMixin.__init__(self, slot, data_type)


# Slot node for Composition
# INHERITED:
#   - input nodes
#   - output nodes
#   - procedure
class ProcNode(Node[InputNode, OutputNode]):

    __proc: Procedure

    # CONSTRUCTOR
    # POST: no inputs
    # POST: no outputs
    # POST: procedure is `proc`
    def __init__(self, proc: Procedure) -> None:
        super().__init__(False, False)
        self.__proc = proc

    # QUERIES
    
    # Get procedure
    def get_proc(self) -> Procedure:
        return self.__proc


def _invalidate_node(node: InputNode | OutputNode | ProcNode):
    if not node.is_valid():
        return
    node.invalidate()
    for output in node.get_outputs():
        _invalidate_node(output)


@final
class Composition(Procedure):

    __input_nodes: dict[str, set[InputNode]]
    __output_nodes: dict[str, OutputNode]
    __input_slots: dict[str, type]
    __output_slots: dict[str, type]
    __needs_run: bool

    ProcDescr = tuple[Procedure, dict[str, str], dict[str, str]]
    
    # CONSTRUCTOR
    @status("OK", "ERROR", name="init")
    def __init__(self, contents: list[ProcDescr]) -> None:
        super().__init__()
        self.__needs_run = True
        self._set_status("init", "OK")

        input_nodes = dict[str, set[InputNode]]()
        output_nodes = dict[str, OutputNode]()
        procedures = set[ProcNode]()
        
        for proc, proc_inputs, proc_outputs in contents:
            proc_node = ProcNode(proc)
            procedures.add(proc_node)
            proc_input_slots = proc.get_input_slots()
            proc_output_slots = proc.get_output_slots()

            for slot, name in proc_inputs.items():
                if name not in input_nodes:
                    input_nodes[name] = set()
                input_node = InputNode(slot, proc_input_slots[slot])
                input_nodes[name].add(input_node)
                input_node.add_output(proc_node)
                proc_node.add_input(input_node)

            for slot, name in proc_outputs.items():
                output_node = OutputNode(slot, proc_output_slots[slot])
                output_nodes[name] = output_node
                proc_node.add_output(output_node)
                output_node.add_input(proc_node)
                if name not in output_nodes:
                    output_nodes[name] = OutputNode(slot, proc_output_slots[slot])
                output_node = output_nodes[name]
                assert _type_fits(proc_output_slots[slot], output_node.get_type())

        internal_names = set[str]()
        for name, output_node in output_nodes.items():
            if name not in input_nodes:
                continue
            for input_node in input_nodes[name]:
                output_node.add_output(input_node)
                input_node.add_input(output_node)
                assert _type_fits(output_node.get_type(), input_node.get_type())
            internal_names.add(name)
        for name in internal_names:
            del input_nodes[name]
            del output_nodes[name]

        self.__input_nodes = input_nodes
        self.__output_nodes = output_nodes
        
        self.__input_slots = dict[str, type]()
        for name, nodes in input_nodes.items():
            t = _type_intersection([node.get_type() for node in nodes])
            assert t
            self.__input_slots[name] = t
        self.__output_slots = dict[str, type]()
        for name, node in output_nodes.items():
            self.__output_slots[name] = node.get_type()

    
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
        if not _type_fits(type(value), self.__input_slots[slot]):
            self._set_status("put", "INVALID_TYPE")
            return
        for input_node in self.__input_nodes[slot]:
            self.__put_data(input_node, value)
            if not self.is_status("put_data", "OK"):
                self._set_status("put", self.get_status("put_data"))
                return
        self.__needs_run = True
        self._set_status("put", "OK")


    # Run procedure
    # PRE: procedure can run successfully with current inputs
    # POST: output values are set
    # POST: input values status set to unchanged
    @status("OK", "INVALID_INPUT", "RUN_FAILED")
    def run(self) -> None:
        for _, node in self.__output_nodes.items():
            self.__validate_output_node(node)
        self.__needs_run = False
        self._set_status("run", "OK")

    
    @status("OK", "INVALID_VALUE", name="put_data")
    def __put_data(self, input_node: InputNode, value: Any) -> None:
        assert len(input_node.get_outputs()) == 1
        proc_node = next(iter(input_node.get_outputs()))
        proc = proc_node.get_proc()
        proc.put(input_node.get_slot(), value)
        if proc.is_status("put", "INVALID_VALUE"):
            self._set_status("put_data", "INVALID_VALUE")
            return
        assert proc.is_status("put", "OK")
        input_node.validate()
        _invalidate_node(proc_node)
        self._set_status("put_data", "OK")


    def __validate_output_node(self, output_node: OutputNode) -> None:
        if output_node.is_valid():
            return
        assert len(output_node.get_inputs()) == 1
        proc_node = next(iter(output_node.get_inputs()))
        self.__validate_proc_node(proc_node)
        output_node.validate()


    def __validate_proc_node(self, proc_node: ProcNode):
        if proc_node.is_valid():
            return
        for input_node in proc_node.get_inputs():
            self.__validate_input_node(input_node)
        proc = proc_node.get_proc()
        proc.run()
        proc_node.validate()
        for output_node in proc_node.get_outputs():
            value = self.__get_data(output_node)
            for dest_node in output_node.get_outputs():
                self.__put_data(dest_node, value)


    def __validate_input_node(self, input_node: InputNode) -> None:
        if input_node.is_valid():
            return
        assert len(input_node.get_inputs()) == 1
        source_node = next(iter(input_node.get_inputs()))
        self.__validate_output_node(source_node)
        input_node.validate()


    def __get_data(self, output_node: OutputNode) -> Any:
        assert len(output_node.get_inputs()) == 1
        proc_node = next(iter(output_node.get_inputs()))
        proc = proc_node.get_proc()
        value = proc.get(output_node.get_slot())
        assert proc.is_status("get", "OK")
        return value


    # QUERIES

    # Get description of input slots
    def get_input_slots(self) -> dict[str, type]:
        return self.__input_slots.copy()

    # Get description of output slots
    def get_output_slots(self) -> dict[str, type]:
        return self.__output_slots.copy()

    # Check if the procedure needs run to update outputs
    def needs_run(self) -> bool:
        return self.__needs_run

    # Get output value
    # PRE: slot is valid output slot name
    # PRE: run was successful after last input change
    @status("OK", "INVALID_SLOT", "NEEDS_RUN")
    def get(self, slot: str) -> Any:
        if slot not in self.__output_nodes:
            self._set_status("get", "INVALID_SLOT")
            return None
        if self.needs_run():
            self._set_status("get", "NEEDS_RUN")
            return None
        output_node = self.__output_nodes[slot]
        value = self.__get_data(output_node)
        self._set_status("get", "OK")
        return value


def _type_fits(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False


def _type_intersection(types: list[type]) -> Optional[type]:
    minor_type = types[0]
    for t in types[1:]:
        if _type_fits(minor_type, t):
            continue
        if not _type_fits(t, minor_type):
            return None
        minor_type = t
    return minor_type
