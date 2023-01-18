from typing import Any, Optional, Union
from enum import Enum, auto
from abc import ABC, abstractmethod


class ValueNode:

    __value_type: type
    __value: Any
    __state: "State"
    __input: Optional["ProcedureNode"]
    __outputs: set["ProcedureNode"]
    __build_complete: bool
    __waiting_outputs: set["ProcedureNode"]

    # CONSTRUCTOR
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
    # PRE: building not complete
    # PRE: node not linked to this
    # PRE: this node has no inputs
    # POST: node linked as input to this
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


    # add outinput node
    # PRE: building not complete
    # PRE: node not linked to this
    # POST: node linked as output to this
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
    # PRE: value of proper type
    # POST: value is set
    # POST: if there are outputs then state is NEW else REGULAR
    # POST: all outputs get invalidate command
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


    # set state to INVALID
    # PRE: build complete
    # POST: state is INVALID
    # POST: if the state has changed then all outputs get invalidate command
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
    # PRE: output is linked
    # PRE: not in INVALID state
    # POST: if state is NEW and all outputs used value then set state to REGULAR
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
    # POST: if the state is INVALID then the input gets run command
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
        self.__input.run()
        if self.__input.get_run_status() != ProcedureNode.RunStatus.OK:
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

    def get_put_status(self) -> PutStatus:
        return self._put_status


    # QUERIES

    # set input value
    # PRE: name is acceptable
    # PRE: all input values are set
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

    def get_get_status(self) -> GetStatus:
        return self._get_status


class ProcedureNode:

    __procedure: Procedure
    __inputs: dict[str, ValueNode]
    __outputs: dict[str, ValueNode]
    __build_complete: bool

    # CONSTRUCTOR
    def __init__(self, procedure: Procedure) -> None:
        self.__procedure = procedure
        self.__inputs = dict()
        self.__outputs = dict()
        self.__build_complete = False
        self.__add_input_status = self.AddInputStatus.NIL
        self.__add_output_status = self.AddOutputStatus.NIL
        self.__invalidate_status = self.InvalidateStatus.NIL
        self.__run_status = self.RunStatus.NIL


    # COMMANDS

    # add input node
    # PRE: building not complete
    # PRE: node not linked to this
    # POST: node linked as input to this
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
    # PRE: building not complete
    # PRE: node not linked to this
    # POST: node linked as output to this
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
    # POST: procedure initialized
    # POST: build complete
    def complete_build(self) -> None:
        self.__build_complete = True


    # signal that input state changed to NEW or INVALID
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
    def run(self) -> None:
        if not self.__build_complete:
            self.__run_status = self.RunStatus.BUILD_INCOMPLETE
            return
        for input in self.__inputs.values():
            input.validate()
            if input.get_validate_status() != ValueNode.ValidateStatus.OK:
                self.__run_status = self.RunStatus.INPUT_VALIDATION_FAILED
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
                self.__run_status = self.RunStatus.FAIL
                return
        for name, output in self.__outputs.items():
            value = self.__procedure.get(name)
            if self.__procedure.get_get_status() != Procedure.GetStatus.OK:
                self.__run_status = self.RunStatus.FAIL
                return
            output.put(value)
            if output.get_put_status() != ValueNode.PutStatus.OK:
                self.__run_status = self.RunStatus.FAIL
                return
        self.__run_status = self.RunStatus.OK
        for input in self.__inputs.values():
            input.used_by(self)
            assert(input.get_used_by_status() == ValueNode.UsedByStatus.OK)

    class RunStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        INPUT_VALIDATION_FAILED = auto(),
        FAIL = auto(),

    __run_status: RunStatus

    def get_run_status(self) -> RunStatus:
        return self.__run_status


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


ValueNodePattern = tuple[str, type]
ProcNodePattern = tuple[Procedure, dict[str, str], dict[str, str]]
NodePattern = Union[ValueNodePattern, ProcNodePattern]

class Simulator(Procedure):

    __values: dict[str, ValueNode]
    __procs: list[ProcedureNode]

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
        self.__put_status = self.PutStatus.NIL
        self.__get_status = self.GetStatus.NIL
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

    __init_status: InitStatus
    __init_message: str

    def get_init_status(self) -> InitStatus:
        return self.__init_status

    def get_init_message(self) -> str:
        return self.__init_message


    def __init_values(self, patterns: list[ValueNodePattern]) -> None:
        self.__values = dict()
        for name, value_type in patterns:
            if name in self.__values:
                self.__init_status = self.InitStatus.DUPLICATE_NAME
                self.__init_message = f"Duplicate name: '{name}'"
                return
            self.__values[name] = ValueNode(value_type)


    def __init_procs(self, patterns: list[ProcNodePattern]) -> None:
        self.__procs = list()
        for proc_type, inputs, outputs in patterns:
            proc = ProcedureNode(proc_type)
            self.__add_inputs(proc, inputs)
            if self.__init_status != self.InitStatus.NIL:
                return
            self.__add_outputs(proc, outputs)
            if self.__init_status != self.InitStatus.NIL:
                return
            self.__procs.append(proc)


    def __add_inputs(self, proc: ProcedureNode, inputs: dict[str, str]) -> None:
        for socket_name, value_name in inputs.items():
            if value_name not in self.__values:
                self.__init_status = self.InitStatus.NAME_NOT_FOUND
                self.__init_message = f"Input not found: '{socket_name}': '{value_name}'"
                return
            value = self.__values[value_name]
            value.add_output(proc)
            if value.get_add_output_status() \
                    == ValueNode.AddOutputStatus.ALREADY_LINKED:
                self.__init_status = self.InitStatus.ALREADY_LINKED
                self.__init_message = f"Already linked: '{socket_name}': '{value_name}'"
                return
            assert(value.get_add_output_status() == ValueNode.AddOutputStatus.OK)
            proc.add_input(socket_name, value)
            if proc.get_add_input_status() \
                    == ProcedureNode.AddInputStatus.ALREADY_LINKED:
                self.__init_status = self.InitStatus.ALREADY_LINKED
                self.__init_message = f"Already linked: '{socket_name}': '{value_name}'"
                return
            assert(proc.get_add_input_status() == ProcedureNode.AddInputStatus.OK)


    def __add_outputs(self, proc: ProcedureNode, outputs: dict[str, str]) -> None:
        for socket_name, value_name in outputs.items():
            if value_name not in self.__values:
                self.__init_status = self.InitStatus.NAME_NOT_FOUND
                self.__init_message = f"Output not found: '{socket_name}': '{value_name}'"
                return
            value = self.__values[value_name]
            proc.add_output(socket_name, value)
            if proc.get_add_output_status() \
                    == ProcedureNode.AddOutputStatus.ALREADY_LINKED:
                self.__init_status = self.InitStatus.ALREADY_LINKED
                self.__init_message = f"Already linked: '{socket_name}': '{value_name}'"
                return
            assert(proc.get_add_output_status() == ProcedureNode.AddOutputStatus.OK)
            value.add_input(proc)
            if value.get_add_input_status() \
                    == ValueNode.AddInputStatus.ALREADY_LINKED:
                self.__init_status = self.InitStatus.ALREADY_LINKED
                self.__init_message = f"Already linked: '{socket_name}': '{value_name}'"
                return
            if value.get_add_input_status() \
                    == ValueNode.AddInputStatus.TOO_MANY_INPUTS:
                self.__init_status = self.InitStatus.TOO_MANY_INPUTS
                self.__init_message = f"Too many inputs: '{socket_name}': '{value_name}'"
                return
            assert(value.get_add_input_status() == ValueNode.AddInputStatus.OK)


    # COMMANDS

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
