from typing import TypeVar, Type, Any, Generic
from abc import abstractmethod
from enum import Enum, auto
from tools import Status, status
from procedures import _type_fits

T = TypeVar("T")

# Interface for data input
# Generic argument is used in `Calculator`
# CONTAINS:
#   - data
#   - data type
#   - data state (no data, new data, used data)
class Input(Generic[T], Status):

    class State(Enum):
        NONE = auto(),
        NEW = auto(),
        USED = auto(),

    # COMMANDS

    # Mark data as used
    # PRE: data state is not `NONE`
    @abstractmethod
    @status("OK", "NO_DATA")
    def mark_used(self) -> None:
        assert False
    
    
    # QUERIES

    # Get data type
    @abstractmethod
    def get_type(self) -> Type[T]:
        assert False

    # Get data state
    @abstractmethod
    def get_state(self) -> State:
        assert False

    # Get data
    # PRE: data state is not `NONE`
    @abstractmethod
    @status("OK", "NO_DATA")
    def get(self) -> T:
        assert False


# Interface for data output
# Generic argument is used in `Calculator`
# CONTAINS:
#   - data
#   - data type
class Output(Generic[T], Status):

    # COMMANDS

    # Set data
    # PRE: `value` type fits data type
    @abstractmethod
    @status("OK", "INVALID_TYPE")
    def set(self, value: T) -> None:
        assert False
    
    
    # QUERIES
    
    # Get data type
    @abstractmethod
    def get_type(self) -> Type[T]:
        assert False


# Slot containing data
# CONTAINS:
#   - data
#   - data type
#   - data state (no data, new data, used data)
class Slot(Input[Any], Output[Any]):
    
    __type: type
    __value: Any
    __state: Input.State

    def __init__(self, data_type: type) -> None:
        super().__init__()
        self.__type = data_type
        self.__state = self.State.NONE

    @status("OK", "INVALID_TYPE")
    def set(self, value: Any) -> None:
        if not _type_fits(type(value), self.__type):
            self._set_status("set", "INVALID_TYPE")
            return
        self._set_status("set", "OK")
        self.__state = self.State.NEW
        self.__value = value

    @status("OK", "NO_DATA")
    def mark_used(self) -> None:
        if self.__state == Input.State.NONE:
            self._set_status("mark_used", "NO_DATA")
            return
        self.__state = self.State.USED
        self._set_status("mark_used", "OK")
    
    def get_type(self) -> Type[Any]:
        return self.__type

    def get_state(self) -> Input.State:
        return self.__state

    @status("OK", "NO_DATA")
    def get(self) -> Any:
        if self.__state == Input.State.NONE:
            self._set_status("get", "NO_DATA")
            return None
        self._set_status("get", "OK")
        return self.__value


# Procedure interface
# CONTAINS:
#   - input slots
#   - output slots
#   - calculations to run
class Procedure(Status):

    # COMMANDS

    # Run calculations
    # PRE: all inputs have data
    # PRE: input data lead to successfull calculation
    # POST: all outputs have data
    @abstractmethod
    @status("OK", "INVALID_INPUT", "INTERNAL_ERROR")
    def run(self) -> None:
        assert False


    # QUERIES

    # Get IDs of input slots
    @abstractmethod
    def get_input_ids(self) -> set[str]:
        assert False

    # Get IDs of output slots
    @abstractmethod
    def get_output_ids(self) -> set[str]:
        assert False

    # Get input slot
    # PRE: `id` is valid input slot ID
    @abstractmethod
    @status("OK", "INVALID_ID")
    def get_input(self, id: str) -> Output[Any]:
        assert False

    # Get output slot
    # PRE: `id` is valid output slot ID
    @abstractmethod
    @status("OK", "INVALID_ID")
    def get_output(self, id: str) -> Input[Any]:
        assert False
