from typing import Any, Optional
from enum import Enum, auto
from abc import abstractmethod


class ValueNode:

    __value_type: type
    __value: Any
    __state: "State"
    __input: Optional["ProcNode"]
    __outputs: set["ProcNode"]
    __build_complete: bool
    __waiting_outputs: set["ProcNode"]

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
    def add_input(self, input: "ProcNode") -> None:
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
    def add_output(self, output: "ProcNode") -> None:
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
        if type(value) is not self.__value_type:
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
                == ProcNode.InvalidateStatus.OK)

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
                == ProcNode.InvalidateStatus.OK)

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
    def used_by(self, output: "ProcNode") -> None:
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
        if self.__input.get_run_status() != ProcNode.RunStatus.OK:
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
    def get_input(self) -> Optional["ProcNode"]:
        return self.__input

    # get set of output nodes
    def get_outputs(self) -> set["ProcNode"]:
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


class ProcIO:

    # QUERIES

    # get dictionary of nodes
    @abstractmethod
    def get_nodes(self) -> dict[str, ValueNode]:
        return dict()
    
    # check if name is in collection
    @abstractmethod
    def has_name(self, name: str) -> bool:
        return False

    # get type of node
    # PRE: node is in the collection
    @abstractmethod
    def get_type(self, name: str) -> type:
        return object

    class GetTypeStatus(Enum):
        NIL = auto(),
        OK = auto(),
        NOT_FOUND = auto(),

    @abstractmethod
    def get_get_type_status(self) -> GetTypeStatus:
        return self.GetTypeStatus.NIL


class ProcInput(ProcIO):
    
    # get value of node
    # PRE: building complete
    # PRE: node is in the collection
    @abstractmethod
    def get(self, name: str) -> Any:
        return object

    class GetStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        NOT_FOUND = auto(),

    @abstractmethod
    def get_get_status(self) -> GetStatus:
        return self.GetTypeStatus.NIL


class ProcOutput(ProcIO):
    
    # COMMANDS
    
    # get type of node
    # PRE: node is in the collection
    @abstractmethod
    def put(self, name: str, value: Any) -> None:
        pass

    class PutStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        NOT_FOUND = auto(),
        INCOMPATIBLE_TYPE = auto(),

    @abstractmethod
    def get_put_status(self) -> PutStatus:
        return self.PutStatus.NIL


class ProcNodeIO(ProcIO):

    _nodes: dict[str, ValueNode]
    _build_complete: bool

    # CONSTRUCTOR
    def __init__(self) -> None:
        self._nodes = dict()
        self._build_complete = False
        self.__add_status = self.AddStatus.NIL
        self.__get_type_status = self.GetTypeStatus.NIL

    
    # COMMANDS
    
    # add node
    # PRE: building not complete
    # PRE: node not in collection
    # PRE: name not in collection
    # POST: node linked as output to this
    def add(self, name: str, node: ValueNode) -> None:
        if self._build_complete:
            self.__add_status = self.AddStatus.BUILD_COMPLETE
            return
        if node in self._nodes.values():
            self.__add_status = self.AddStatus.DUPLICATE_NODE
            return
        if name in self._nodes:
            self.__add_status = self.AddStatus.DUPLICATE_NAME
            return
        self._nodes[name] = node
        self.__add_status = self.AddStatus.OK
    
    class AddStatus(Enum):
        NIL = auto(),
        OK = auto(),
        DUPLICATE_NODE = auto(),
        DUPLICATE_NAME = auto(),
        BUILD_COMPLETE = auto(),

    __add_status: AddStatus

    def get_add_status(self) -> AddStatus:
        return self.__add_status


    # complete build
    # POST: build complete
    def complete_build(self) -> None:
        self._build_complete = True


    # QUERIES

    # get dictionary of nodes
    def get_nodes(self) -> dict[str, ValueNode]:
        return self._nodes.copy()

    # check if name is in collection
    def has_name(self, name: str) -> bool:
        return name in self._nodes

    # check if node is in collection
    def has_node(self, node: ValueNode) -> bool:
        return node in self._nodes.values()

    # check if name is in collection
    def get_type(self, name: str) -> type:
        if name not in self._nodes:
            self.__get_type_status = self.GetTypeStatus.NOT_FOUND
            return object
        self.__get_type_status = self.GetTypeStatus.OK
        return self._nodes[name].get_type()

    __get_type_status: ProcOutput.GetTypeStatus

    def get_get_type_status(self) -> ProcOutput.GetTypeStatus:
        return self.__get_type_status


class ProcNodeInput(ProcNodeIO, ProcInput):

    # CONSTRUCTOR
    def __init__(self) -> None:
        super().__init__()
        self.__get_status = self.GetStatus.NIL

    def get(self, name: str) -> Any:
        if not self._build_complete:
            self.__get_status = self.GetStatus.BUILD_INCOMPLETE
            return
        if not self.has_name(name):
            self.__get_status = self.GetStatus.NOT_FOUND
            return
        self.__get_status = self.GetStatus.OK
        value = self._nodes[name].get()
        assert(self._nodes[name].get_get_status() == ValueNode.GetStatus.OK)
        return value

    __get_status: ProcInput.GetStatus

    def get_get_status(self) -> ProcInput.GetStatus:
        return self.__get_status


class ProcNodeOutput(ProcNodeIO, ProcOutput):

    __incomplete_outputs: set[str]

    # CONSTRUCTOR
    def __init__(self) -> None:
        super().__init__()
        self.__incomplete_outputs = set()
        self.__put_status = self.PutStatus.NIL
        self.__reset_output_check_status = self.ResetOutputCheckStatus.NIL
        self.__is_output_complete_status = self.IsOutputCompleteStatus.NIL


    # COMMANDS
    
    # get type of node
    # PRE: node is in the collection
    def put(self, name: str, value: Any) -> None:
        if not self._build_complete:
            self.__put_status = self.PutStatus.BUILD_INCOMPLETE
            return
        if not self.has_name(name):
            self.__put_status = self.PutStatus.NOT_FOUND
            return
        if not issubclass(type(value), self.get_type(name)):
            self.__put_status = self.PutStatus.INCOMPATIBLE_TYPE
            return
        self.__put_status = self.PutStatus.OK
        self._nodes[name].put(value)
        assert(self._nodes[name].get_put_status() == ValueNode.PutStatus.OK)
        if name in self.__incomplete_outputs:
            self.__incomplete_outputs.remove(name)

    __put_status: ProcOutput.PutStatus

    @abstractmethod
    def get_put_status(self) -> ProcOutput.PutStatus:
        return self.__put_status

    
    # reset node-put-value status
    def reset_output_check(self) -> None:
        if not self._build_complete:
            self.__reset_output_check_status = \
                self.ResetOutputCheckStatus.BUILD_INCOMPLETE
            return
        self.__reset_output_check_status = self.ResetOutputCheckStatus.OK
        self.__incomplete_outputs = set(self._nodes.keys())

    class ResetOutputCheckStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),

    __reset_output_check_status: ResetOutputCheckStatus

    def get_reset_output_check_status(self) -> ResetOutputCheckStatus:
        return self.__reset_output_check_status


    # QUERIES

    # check if values were put to all nodes
    def is_output_complete(self) -> bool:
        if not self._build_complete:
            self.__is_output_complete_status = \
                self.IsOutputCompleteStatus.BUILD_INCOMPLETE
            return False
        self.__is_output_complete_status = self.IsOutputCompleteStatus.OK
        return len(self.__incomplete_outputs) == 0

    class IsOutputCompleteStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),

    __is_output_complete_status: IsOutputCompleteStatus

    def get_is_output_complete_status(self) -> IsOutputCompleteStatus:
        return self.__is_output_complete_status


class ProcNode:

    __proc_type: type
    __proc: Any
    __inputs: ProcNodeInput
    __outputs: ProcNodeOutput
    __build_complete: bool

    # CONSTRUCTOR
    def __init__(self, proc_type: type) -> None:
        self.__proc_type = proc_type
        self.__inputs = ProcNodeInput()
        self.__outputs = ProcNodeOutput()
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
        if self.__inputs.has_node(input) or self.__outputs.has_node(input):
            self.__add_input_status = self.AddInputStatus.ALREADY_LINKED
            return
        if self.__inputs.has_name(name) or self.__outputs.has_name(name):
            self.__add_input_status = self.AddInputStatus.DUPLICATE_NAME
            return
        self.__inputs.add(name, input)
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
        if self.__inputs.has_node(output) or self.__outputs.has_node(output):
            self.__add_output_status = self.AddOutputStatus.ALREADY_LINKED
            return
        if self.__inputs.has_name(name) or self.__outputs.has_name(name):
            self.__add_output_status = self.AddOutputStatus.DUPLICATE_NAME
            return
        self.__outputs.add(name, output)
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
        self.__outputs.complete_build()
        self.__proc = self.__proc_type(self.__inputs, self.__outputs)
        self.__build_complete = True


    # signal that input state changed to NEW or INVALID
    def invalidate(self) -> None:
        if not self.__build_complete:
            self.__invalidate_status = self.InvalidateStatus.BUILD_INCOMPLETE
            return
        self.__invalidate_status = self.InvalidateStatus.OK
        for output in self.__outputs.get_nodes().values():
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
        for input in self.__inputs.get_nodes().values():
            input.validate()
            assert(input.get_validate_status() == ValueNode.ValidateStatus.OK)
        self.__outputs.reset_output_check()
        self.__proc.run()
        if not self.__outputs.is_output_complete():
            self.__run_status = self.RunStatus.INCOMPLETE_OUTPUT
            return
        self.__run_status = self.RunStatus.OK
        for input in self.__inputs.get_nodes().values():
            input.used_by(self)
            assert(input.get_used_by_status() == ValueNode.UsedByStatus.OK)

    class RunStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        INCOMPLETE_OUTPUT = auto(),

    __run_status: RunStatus

    def get_run_status(self) -> RunStatus:
        return self.__run_status


    # QUERIES

    # get dictionary of input nodes
    def get_inputs(self) -> dict[str, "ValueNode"]:
        return self.__inputs.get_nodes()

    # get dictionary of output nodes
    def get_outputs(self) -> dict[str, "ValueNode"]:
        return self.__outputs.get_nodes()
