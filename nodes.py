from typing import Any, Optional
from enum import Enum, auto


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
    # POST: all outputs get command input_state_change
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
            output.input_state_change()
            assert(output.get_input_state_change_status() \
                == ProcNode.InputStateChangeStatus.OK)

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
    # POST: if the state has changed then all outputs get command input_state_change
    def invalidate(self) -> None:
        if not self.__build_complete:
            self.__invalidate_status = self.InvalidateStatus.BUILD_INCOMPLETE
            return
        self.__invalidate_status = self.InvalidateStatus.OK
        if self.__state == self.State.INVALID:
            return
        self.__state = self.State.INVALID
        for output in self.__outputs:
            output.input_state_change()
            assert(output.get_input_state_change_status() \
                == ProcNode.InputStateChangeStatus.OK)

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
        if self.__state == self.State.INVALID and self.__input is None:
            self.__validate_status = self.ValidateStatus.NO_VALUE_SOURCE
            return
        if self.__state == self.State.INVALID:
            assert(self.__input)
            self.__input.run()
            assert(self.__input.get_run_status() == ProcNode.RunStatus.OK)
        self.__validate_status = self.ValidateStatus.OK

    class ValidateStatus(Enum):
        NIL = auto(),
        OK = auto(),
        BUILD_INCOMPLETE = auto(),
        NO_VALUE_SOURCE = auto(),

    __validate_status: ValidateStatus

    def get_validate_status(self) -> ValidateStatus:
        return self.__validate_status


    # QUERIES

    # get input node
    def get_input(self) -> Optional["ProcNode"]:
        return self.__input

    # get set of output nodes
    def get_outputs(self) -> set["ProcNode"]:
        return self.__outputs


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


class ProcNode:

    # CONSTRUCTOR
    def __init__(self, proc_type: type) -> None:
        self.__input_state_change_status = self.InputStateChangeStatus.NIL
        self.__run_status = self.RunStatus.NIL


    # COMMANDS

    # complete build
    # POST: procedure initialized
    # POST: build complete
    def complete_build(self) -> None:
        pass

    
    # process update of input state change to NEW or INVALID
    def input_state_change(self) -> None:
        self.__input_state_change_status = self.InputStateChangeStatus.OK

    class InputStateChangeStatus(Enum):
        NIL = auto(),
        OK = auto(),

    __input_state_change_status: InputStateChangeStatus

    def get_input_state_change_status(self) -> InputStateChangeStatus:
        return self.__input_state_change_status

    
    # run the procedure
    def run(self) -> None:
        self.__run_status = self.RunStatus.OK

    class RunStatus(Enum):
        NIL = auto(),
        OK = auto(),

    __run_status: RunStatus

    def get_run_status(self) -> RunStatus:
        return self.__run_status
