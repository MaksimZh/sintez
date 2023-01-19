from typing import Any, Optional, Union, final
from enum import Enum, auto
from abc import ABC, abstractmethod

# Nodes implement the calculation scheme logic.
#
# ValueNode can be linked only to ProcedureNodes and vice versa.
# All links have one and only one direction, no loops allowed.
# The basic concepts of calculation are invalidation and validation.
# Value change invalidates all succeeding nodes.
# Procedure validation also validates all its output nodes.
# When node is invalidated it invalidates all succeeding nodes.
# When node is validated it requests validation of all preceding nodes.
#
# When node is created its build is incomplete.
# Inputs and outputs can be added only before build is complete.
# Manipulations concerning calculation logic are forbidden until build is complete.


# Implements value node part of calculation scheme logic.
# Can have only one (optional) input procedure.
# So there is only one component responsible for value update.
#
# Contains:
#     - input procedure node (optional)
#     - output procedure nodes (any number)
#     - value type
#     - build status
#     - value state (INVALID, NEW, REGULAR)
#     - value (optional)
#     - outputs that have not used NEW value
#
@final
class ValueNode:

    __value_type: type
    __value: Any
    __state: "State"
    __input: Optional["ProcedureNode"]
    __outputs: set["ProcedureNode"]
    __build_complete: bool
    __waiting_outputs: set["ProcedureNode"]

    # CONSTRUCTOR
    # POST: no input node
    # POST: no output nodes
    # POST: value type is set
    # POST: build not complete
    def __init__(self, value_type: type) -> None:
        self.__value_type = value_type
        self.__state = self.State.INVALID
        self.__input = None
        self.__outputs = set()
        self.__waiting_outputs = set()
        self.__build_complete = False
        self.__add_input_status = self.AddInputStatus.NIL
        self.__add_output_status = self.AddOutputStatus.NIL
        self.__put_status = self.PutStatus.NIL
        self.__invalidate_status = self.InvalidateStatus.NIL
        self.__used_by_status = self.UsedByStatus.NIL
        self.__validate_status = self.ValidateStatus.NIL
        self.__get_state_status = self.GetStateStatus.NIL
        self.__get_status = self.GetStatus.NIL


    # COMMANDS

    # add input node
    # PRE: build not complete
    # PRE: 'input' is not in input or outputs
    # PRE: this node has no inputs
    # POST: input is set to 'input'
    def add_input(self, input: "ProcedureNode") -> None:
        if self.__build_complete:
            self.__add_input_status = self.AddInputStatus.BUILD_COMPLETE
            return
        if input in self.__outputs or input is self.__input:
            self.__add_input_status = self.AddInputStatus.ALREADY_LINKED
            return
        if self.__input is not None:
            self.__add_input_status = self.AddInputStatus.TOO_MANY_INPUTS
            return
        self.__input = input
        self.__add_input_status = self.AddInputStatus.OK

    class AddInputStatus(Enum):
        NIL = auto(),
        OK = auto(),
        ALREADY_LINKED = auto(),
        TOO_MANY_INPUTS = auto(),
        BUILD_COMPLETE = auto(),

    __add_input_status: AddInputStatus

    def get_add_input_status(self) -> AddInputStatus:
        return self.__add_input_status


    # add output node
    # PRE: build not complete
    # PRE: 'output' is not in input or outputs
    # POST: 'output' added to output nodes
    def add_output(self, output: "ProcedureNode") -> None:
        if self.__build_complete:
            self.__add_output_status = self.AddOutputStatus.BUILD_COMPLETE
            return
        if output in self.__outputs or output is self.__input:
            self.__add_output_status = self.AddOutputStatus.ALREADY_LINKED
            return
        self.__outputs.add(output)
        self.__add_output_status = self.AddOutputStatus.OK

    class AddOutputStatus(Enum):
        NIL = auto(),
        OK = auto(),
        ALREADY_LINKED = auto(),
        BUILD_COMPLETE = auto(),

    __add_output_status: AddOutputStatus

    def get_add_output_status(self) -> AddOutputStatus:
        return self.__add_output_status


    # complete build
    # POST: build complete
    # POST: state is INVALID
    def complete_build(self) -> None:
        self.__build_complete = True


    # put value
    # PRE: build complete
    # PRE: 'value' can be implicitly converted to node type
    # POST: if there are outputs then state is NEW else REGULAR
    # POST: value is set to 'value'
    # POST: send invalidate command to all outputs
    # POST: no outputs used NEW value
    def put(self, value: Any) -> None:
        if not self.__build_complete:
            self.__put_status = self.PutStatus.BUILD_INCOMPLETE
            return
        if not _type_fits(type(value), self.__value_type):
            self.__put_status = self.PutStatus.INCOMPATIBLE_TYPE
            return
        self.__put_status = self.PutStatus.OK
        self.__value = value
        self.__state = self.State.REGULAR if len(self.__outputs) == 0 else \
            self.State.NEW
        for output in self.__outputs:
            self.__waiting_outputs.add(output)
            output.invalidate()
            assert(output.get_invalidate_status() \
                == ProcedureNode.InvalidateStatus.OK)

    class PutStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        INCOMPATIBLE_TYPE = auto(),

    __put_status: PutStatus

    def get_put_status(self) -> PutStatus:
        return self.__put_status


    # invalidate node
    # PRE: build complete
    # POST: state is INVALID
    # POST: if the state has changed then send invalidate command to all outputs
    def invalidate(self) -> None:
        if not self.__build_complete:
            self.__invalidate_status = self.InvalidateStatus.BUILD_INCOMPLETE
            return
        self.__invalidate_status = self.InvalidateStatus.OK
        if self.__state == self.State.INVALID:
            return
        self.__state = self.State.INVALID
        for output in self.__outputs:
            output.invalidate()
            assert(output.get_invalidate_status() \
                == ProcedureNode.InvalidateStatus.OK)

    class InvalidateStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),

    __invalidate_status: InvalidateStatus

    def get_invalidate_status(self) -> InvalidateStatus:
        return self.__invalidate_status


    # notify that the value was used by output
    # PRE: build complete
    # PRE: 'output' is in outputs
    # PRE: state is not INVALID
    # POST: 'output' used new value
    # POST: if all outputs used the value then set state to REGULAR
    def used_by(self, output: "ProcedureNode") -> None:
        if not self.__build_complete:
            self.__used_by_status = self.UsedByStatus.BUILD_INCOMPLETE
            return
        if output not in self.__outputs:
            self.__used_by_status = self.UsedByStatus.NOT_OUTPUT
            return
        if self.__state is self.State.INVALID:
            self.__used_by_status = self.UsedByStatus.INVALID_VALUE
            return
        self.__waiting_outputs.remove(output)
        if len(self.__waiting_outputs) == 0:
            self.__state = self.State.REGULAR
        self.__used_by_status = self.UsedByStatus.OK

    class UsedByStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        NOT_OUTPUT = auto(),
        INVALID_VALUE = auto(),

    __used_by_status: UsedByStatus

    def get_used_by_status(self) -> UsedByStatus:
        return self.__used_by_status


    # ensure that the value is valid
    # PRE: build complete
    # PRE: there is input or the state is not INVALID
    # POST: if the state is INVALID then send validate command to input
    def validate(self) -> None:
        if not self.__build_complete:
            self.__validate_status = self.ValidateStatus.BUILD_INCOMPLETE
            return
        if self.__state != self.State.INVALID:
            self.__validate_status = self.ValidateStatus.OK
            return
        if self.__input is None:
            self.__validate_status = self.ValidateStatus.NO_VALUE_SOURCE
            return
        assert(self.__input)
        self.__input.validate()
        if self.__input.get_validate_status() != ProcedureNode.ValidateStatus.OK:
            self.__validate_status = self.ValidateStatus.INPUT_FAILED
            return
        self.__validate_status = self.ValidateStatus.OK

    class ValidateStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        NO_VALUE_SOURCE = auto(),
        INPUT_FAILED = auto(),

    __validate_status: ValidateStatus

    def get_validate_status(self) -> ValidateStatus:
        return self.__validate_status


    # QUERIES

    # get value type
    def get_type(self) -> type:
        return self.__value_type

    # get input node
    def get_input(self) -> Optional["ProcedureNode"]:
        return self.__input

    # get set of output nodes
    def get_outputs(self) -> set["ProcedureNode"]:
        return self.__outputs.copy()


    class State(Enum):
        INVALID = auto(),
        NEW = auto(),
        REGULAR = auto(),

    # get node state
    # PRE: build complete
    def get_state(self) -> State:
        if not self.__build_complete:
            self.__get_state_status = self.GetStateStatus.BUILD_INCOMPLETE
            return self.State.INVALID
        self.__get_state_status = self.GetStateStatus.OK
        return self.__state

    class GetStateStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),

    __get_state_status: GetStateStatus

    def get_get_state_status(self) -> GetStateStatus:
        return self.__get_state_status


    # get value
    # PRE: build complete
    # PRE: state is not INVALID
    def get(self) -> Any:
        if not self.__build_complete:
            self.__get_status = self.GetStatus.BUILD_INCOMPLETE
            return None
        if self.__state == self.State.INVALID:
            self.__get_status = self.GetStatus.INVALID_VALUE
            return None
        self.__get_status = self.GetStatus.OK
        return self.__value

    class GetStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        INVALID_VALUE = auto(),

    __get_status: GetStatus

    def get_get_status(self) -> GetStatus:
        return self.__get_status


# Base class for the internal procedure of ProcedureNode
# 
# When the user gets any output value it must be up to date with input values.
#
# Contains:
#     - named and typed input values
#     - named output values 
#
class Procedure(ABC):

    def __init__(self) -> None:
        self._put_status = self.PutStatus.NIL
        self._get_status = self.GetStatus.NIL


    # COMMANDS
    
    # set input value
    # PRE: name is acceptable
    # PRE: value type is compatible
    # POST: input value is set
    @abstractmethod
    def put(self, name: str, value: Any) -> None:
        pass

    class PutStatus(Enum):
        NIL = auto(),
        OK = auto(),
        INVALID_NAME = auto(),
        INCOMPATIBLE_TYPE = auto(),
        INTERNAL_ERROR = auto(),

    _put_status: PutStatus

    @final
    def get_put_status(self) -> PutStatus:
        return self._put_status


    # QUERIES

    # get value
    # PRE: name is acceptable
    # PRE: there is enough data to calculate value
    @abstractmethod
    def get(self, name: str) -> Any:
        pass

    class GetStatus(Enum):
        NIL = auto(),
        OK = auto(),
        INVALID_NAME = auto(),
        INCOMPLETE_INPUT = auto(),
        INTERNAL_ERROR = auto(),

    _get_status: GetStatus

    @final
    def get_get_status(self) -> GetStatus:
        return self._get_status


# Implements procedure node part of calculation scheme logic.
#
# Contains:
#     - input value nodes (any number)
#     - output procedure nodes (any number)
#     - build status
#     - procedure
#
@final
class ProcedureNode:

    __procedure: Procedure
    __inputs: dict[str, ValueNode]
    __outputs: dict[str, ValueNode]
    __build_complete: bool

    # CONSTRUCTOR
    # POST: no input nodes
    # POST: no output nodes
    # POST: procedure is set
    # POST: build not complete
    def __init__(self, procedure: Procedure) -> None:
        self.__procedure = procedure
        self.__inputs = dict()
        self.__outputs = dict()
        self.__build_complete = False
        self.__add_input_status = self.AddInputStatus.NIL
        self.__add_output_status = self.AddOutputStatus.NIL
        self.__invalidate_status = self.InvalidateStatus.NIL
        self.__validate_status = self.ValidateStatus.NIL


    # COMMANDS

    # add input node
    # PRE: build not complete
    # PRE: 'input' is not in inputs or outputs
    # PRE: 'name' is not occupied
    # POST: 'input' added to inputs with 'name'
    def add_input(self, name: str, input: ValueNode) -> None:
        if self.__build_complete:
            self.__add_input_status = self.AddInputStatus.BUILD_COMPLETE
            return
        if self.__is_node_linked(input):
            self.__add_input_status = self.AddInputStatus.ALREADY_LINKED
            return
        if self.__is_slot_linked(name):
            self.__add_input_status = self.AddInputStatus.DUPLICATE_NAME
            return
        self.__inputs[name] = input
        self.__add_input_status = self.AddInputStatus.OK

    class AddInputStatus(Enum):
        NIL = auto(),
        OK = auto(),
        ALREADY_LINKED = auto(),
        DUPLICATE_NAME = auto(),
        BUILD_COMPLETE = auto(),

    __add_input_status: AddInputStatus

    def get_add_input_status(self) -> AddInputStatus:
        return self.__add_input_status


    # add output node
    # PRE: build not complete
    # PRE: 'output' is not in inputs or outputs
    # PRE: 'name' is not occupied
    # POST: 'output' added to outputs with 'name'
    def add_output(self, name: str, output: ValueNode) -> None:
        if self.__build_complete:
            self.__add_output_status = self.AddOutputStatus.BUILD_COMPLETE
            return
        if self.__is_node_linked(output):
            self.__add_output_status = self.AddOutputStatus.ALREADY_LINKED
            return
        if self.__is_slot_linked(name):
            self.__add_output_status = self.AddOutputStatus.DUPLICATE_NAME
            return
        self.__outputs[name] = output
        self.__add_output_status = self.AddOutputStatus.OK

    class AddOutputStatus(Enum):
        NIL = auto(),
        OK = auto(),
        ALREADY_LINKED = auto(),
        DUPLICATE_NAME = auto(),
        BUILD_COMPLETE = auto(),

    __add_output_status: AddOutputStatus

    def get_add_output_status(self) -> AddOutputStatus:
        return self.__add_output_status


    # complete build
    # POST: build complete
    def complete_build(self) -> None:
        self.__build_complete = True


    # signal that input state changed to NEW or INVALID
    # PRE: build complete
    # POST: all outputs get invalidate command
    def invalidate(self) -> None:
        if not self.__build_complete:
            self.__invalidate_status = self.InvalidateStatus.BUILD_INCOMPLETE
            return
        self.__invalidate_status = self.InvalidateStatus.OK
        for output in self.__outputs.values():
            output.invalidate()
            assert(output.get_invalidate_status() \
                == ValueNode.InvalidateStatus.OK)

    class InvalidateStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),

    __invalidate_status: InvalidateStatus

    def get_invalidate_status(self) -> InvalidateStatus:
        return self.__invalidate_status


    # run the procedure
    # PRE: build complete
    # PRE: inputs can be validated
    # PRE: inputs and outputs names and types compatible with the procedure
    # POST: all inputs have been validated
    # POST: inputs in NEW state were sent to procedure with set command
    # POST: all outputs have been updated using procedure get query
    def validate(self) -> None:
        if not self.__build_complete:
            self.__validate_status = self.ValidateStatus.BUILD_INCOMPLETE
            return
        for input in self.__inputs.values():
            input.validate()
            if input.get_validate_status() != ValueNode.ValidateStatus.OK:
                self.__validate_status = self.ValidateStatus.INPUT_VALIDATION_FAILED
                return
        for name, input in self.__inputs.items():
            state = input.get_state()
            assert(input.get_get_state_status() == ValueNode.GetStateStatus.OK)
            if state == ValueNode.State.REGULAR:
                continue
            assert(state == ValueNode.State.NEW)
            value = input.get()
            assert(input.get_get_status() == ValueNode.GetStatus.OK)
            self.__procedure.put(name, value)
            if self.__procedure.get_put_status() != Procedure.PutStatus.OK:
                self.__validate_status = self.ValidateStatus.FAIL
                return
        for name, output in self.__outputs.items():
            value = self.__procedure.get(name)
            if self.__procedure.get_get_status() != Procedure.GetStatus.OK:
                self.__validate_status = self.ValidateStatus.FAIL
                return
            output.put(value)
            if output.get_put_status() != ValueNode.PutStatus.OK:
                self.__validate_status = self.ValidateStatus.FAIL
                return
        self.__validate_status = self.ValidateStatus.OK
        for input in self.__inputs.values():
            input.used_by(self)
            assert(input.get_used_by_status() == ValueNode.UsedByStatus.OK)

    class ValidateStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        INPUT_VALIDATION_FAILED = auto(),
        FAIL = auto(),

    __validate_status: ValidateStatus

    def get_validate_status(self) -> ValidateStatus:
        return self.__validate_status


    # QUERIES

    # get dictionary of input nodes
    def get_inputs(self) -> dict[str, "ValueNode"]:
        return self.__inputs.copy()

    # get dictionary of output nodes
    def get_outputs(self) -> dict[str, "ValueNode"]:
        return self.__outputs.copy()


    def __is_node_linked(self, node: ValueNode) -> bool:
        return node in self.__inputs.values() \
            or node in self.__outputs.values()

    def __is_slot_linked(self, name: str) -> bool:
        return name in self.__inputs \
            or name in self.__outputs


ValueLink = Union[str, type]
ValuePattern = tuple[str, type]
ProcPattern = tuple[Procedure, dict[str, ValueLink], dict[str, ValueLink]]
NodePattern = Union[ValuePattern, ProcPattern]

# Special kind of procedure that contains calculation scheme built using
# its declarative description sent to constructor.
#
# The description is list of value and procedure patterns.
# Value pattern is the following tuple:
#     ("name", ValueType).
# Procedure pattern is the following tuple:
#     (ProcedureType, <input_dictionary>, <output_dictionary>).
# Entries in input and output dictionaries are of the following two kinds:
#     "name_in_procedure": "value_node_name" - link to value node by name
#     "name_in_procedure_and_outside": Type - create value node and link to it
# If the second kind of I/O entry is used in multiple places with the same name
# then their types must match. 
#
class Simulator(Procedure):

    __values: dict[str, ValueNode]
    __procs: list[ProcedureNode]
    __auto_value_types: dict[str, type]

    # CONSTRUCTOR
    # PRE: patterns have no duplicate names
    # PRE: all procedure IO names present in value patterns
    # PRE: no duplicate links
    # PRE: no multiple value inputs
    # POST: nodes linked and build complete for all nodes
    def __init__(self, node_patterns: list[NodePattern]) -> None:
        super().__init__()
        self.__init_status = self.InitStatus.NIL
        self.__init_message = ""
        value_patterns = []
        proc_patterns = []
        for pattern in node_patterns:
            match pattern:
                case (_, _):
                    value_patterns.append(pattern)
                case (_, _, _):
                    proc_patterns.append(pattern)

        self.__init_values(value_patterns)
        if self.__init_status != self.InitStatus.NIL:
            return
        self.__init_procs(proc_patterns)
        if self.__init_status != self.InitStatus.NIL:
            return
        for value in self.__values.values():
            value.complete_build()
        for proc in self.__procs:
            proc.complete_build()
        self.__init_status = self.InitStatus.OK

    class InitStatus(Enum):
        NIL = auto(),
        OK = auto(),
        DUPLICATE_NAME = auto(),
        NAME_NOT_FOUND = auto(),
        ALREADY_LINKED = auto(),
        TOO_MANY_INPUTS = auto(),
        AUTO_VALUE_TYPE_MISMATCH = auto(),

    __init_status: InitStatus
    __init_message: str

    @final
    def get_init_status(self) -> InitStatus:
        return self.__init_status

    @final
    def get_init_message(self) -> str:
        return self.__init_message


    def __init_values(self, patterns: list[ValuePattern]) -> None:
        self.__values = dict()
        for name, value_type in patterns:
            if name in self.__values:
                self.__init_status = self.InitStatus.DUPLICATE_NAME
                self.__init_message = f"Duplicate name: '{name}'"
                return
            self.__values[name] = ValueNode(value_type)


    def __init_procs(self, patterns: list[ProcPattern]) -> None:
        self.__procs = list()
        self.__auto_value_types = dict()
        for proc_type, inputs, outputs in patterns:
            proc = ProcedureNode(proc_type)
            self.__add_inputs(proc, inputs)
            if self.__init_status != self.InitStatus.NIL:
                return
            self.__add_outputs(proc, outputs)
            if self.__init_status != self.InitStatus.NIL:
                return
            self.__procs.append(proc)


    def __add_inputs(self, proc: ProcedureNode, inputs: dict[str, ValueLink]) -> None:
        for slot_name, value_link in inputs.items():
            if type(value_link) is type:
                value_name = slot_name
                self.__add_auto_value(value_name, value_link)
                if self.__init_status != self.InitStatus.NIL:
                    return
            else:
                assert(type(value_link) is str)
                value_name: str = value_link
            if value_name not in self.__values:
                self.__init_status = self.InitStatus.NAME_NOT_FOUND
                self.__init_message = f"Input not found: '{slot_name}': '{value_name}'"
                return
            value = self.__values[value_name]
            self.__add_input(proc, slot_name, value)
            if self.__init_status == self.InitStatus.ALREADY_LINKED:
                self.__init_message = f"Already linked: '{slot_name}': '{value_name}'"
                return

    def __add_outputs(self, proc: ProcedureNode, outputs: dict[str, ValueLink]) -> None:
        for slot_name, value_link in outputs.items():
            if type(value_link) is type:
                value_name = slot_name
                self.__add_auto_value(value_name, value_link)
                if self.__init_status != self.InitStatus.NIL:
                    return
            else:
                assert(type(value_link) is str)
                value_name: str = value_link
            if value_name not in self.__values:
                self.__init_status = self.InitStatus.NAME_NOT_FOUND
                self.__init_message = f"Output not found: '{slot_name}': '{value_name}'"
                return
            value = self.__values[value_name]
            self.__add_output(proc, slot_name, value)
            if self.__init_status == self.InitStatus.ALREADY_LINKED:
                self.__init_message = f"Already linked: '{slot_name}': '{value_name}'"
                return
            if self.__init_status == self.InitStatus.TOO_MANY_INPUTS:
                self.__init_message = f"Too many inputs: '{slot_name}': '{value_name}'"
                return

    def __add_auto_value(self, name: str, value_type: type) -> None:
        if name not in self.__values:
            assert(name not in self.__auto_value_types)
            self.__auto_value_types[name] = value_type
            self.__values[name] = ValueNode(value_type)
            return
        assert(name in self.__auto_value_types)
        if self.__auto_value_types[name] is not value_type:
            self.__init_status = self.InitStatus.AUTO_VALUE_TYPE_MISMATCH
            self.__init_message = \
                f"Auto value '{name}' type mismatch:" + \
                    f" {str(value_type)} and {str(self.__auto_value_types[name])}"

    def __add_input(self, proc: ProcedureNode, slot_name: str, value: ValueNode) -> None:
        value.add_output(proc)
        if value.get_add_output_status() \
                == ValueNode.AddOutputStatus.ALREADY_LINKED:
            self.__init_status = self.InitStatus.ALREADY_LINKED
            return
        assert(value.get_add_output_status() == ValueNode.AddOutputStatus.OK)
        proc.add_input(slot_name, value)
        if proc.get_add_input_status() \
                == ProcedureNode.AddInputStatus.ALREADY_LINKED:
            self.__init_status = self.InitStatus.ALREADY_LINKED
            return
        assert(proc.get_add_input_status() == ProcedureNode.AddInputStatus.OK)

    def __add_output(self, proc: ProcedureNode, slot_name: str, value: ValueNode) -> None:
        proc.add_output(slot_name, value)
        if proc.get_add_output_status() \
                == ProcedureNode.AddOutputStatus.ALREADY_LINKED:
            self.__init_status = self.InitStatus.ALREADY_LINKED
            return
        assert(proc.get_add_output_status() == ProcedureNode.AddOutputStatus.OK)
        value.add_input(proc)
        if value.get_add_input_status() \
                == ValueNode.AddInputStatus.ALREADY_LINKED:
            self.__init_status = self.InitStatus.ALREADY_LINKED
            return
        if value.get_add_input_status() \
                == ValueNode.AddInputStatus.TOO_MANY_INPUTS:
            self.__init_status = self.InitStatus.TOO_MANY_INPUTS
            return
        assert(value.get_add_input_status() == ValueNode.AddInputStatus.OK)


    # COMMANDS

    @final
    def put(self, name: str, value: Any) -> None:
        if self.get_init_status() != self.InitStatus.OK:
            self._put_status = self.PutStatus.INTERNAL_ERROR
            return
        if name not in self.__values:
            self._put_status = self.PutStatus.INVALID_NAME
            return
        if self.__values[name].get_input() is not None:
            self._put_status = self.PutStatus.INVALID_NAME
            return
        self.__values[name].put(value)
        assert(self.__values[name].get_put_status() == ValueNode.PutStatus.OK)
        self._put_status = self.PutStatus.OK


    # QUERIES

    @final
    def get(self, name: str) -> Any:
        if self.get_init_status() != self.InitStatus.OK:
            self._get_status = self.GetStatus.INTERNAL_ERROR
            return
        if name not in self.__values:
            self._get_status = self.GetStatus.INVALID_NAME
            return
        node = self.__values[name]
        node.validate()
        if node.get_validate_status() != ValueNode.ValidateStatus.OK:
            self._get_status = self.GetStatus.INCOMPLETE_INPUT
            return None
        value = node.get()
        assert(node.get_get_status() == ValueNode.GetStatus.OK)
        self._get_status = self.GetStatus.OK
        return value


def _type_fits(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False
