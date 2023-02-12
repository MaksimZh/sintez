from typing import TypeVar, Type, Any, Generic
from abc import abstractmethod
from enum import Enum, auto
from tools import Status, status


T = TypeVar("T")

# Interface for data input
# Generic argument is used in `Calculator`
# CONTAINS:
#   - data
#   - data type
#   - data state (no data, new data, used data)
class DataSource(Generic[T], Status):

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
class DataDest(Generic[T], Status):

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
class Slot(DataSource[Any], DataDest[Any]):
    
    __type: type
    __value: Any
    __state: DataSource.State
    
    
    # CONSTRUCTOR
    # POST: data type is `data_type`
    # POST: state is `NONE`
    def __init__(self, data_type: type) -> None:
        super().__init__()
        self.__type = data_type
        self.__state = self.State.NONE

    
    # COMMANDS

    # Set data
    # PRE: `value` type fits data type
    @status("OK", "INVALID_TYPE")
    def set(self, value: Any) -> None:
        if not _type_fits(type(value), self.__type):
            self._set_status("set", "INVALID_TYPE")
            return
        self._set_status("set", "OK")
        self.__state = self.State.NEW
        self.__value = value

    # Mark data as used
    # PRE: data state is not `NONE`
    @status("OK", "NO_DATA")
    def mark_used(self) -> None:
        if self.__state == DataSource.State.NONE:
            self._set_status("mark_used", "NO_DATA")
            return
        self.__state = self.State.USED
        self._set_status("mark_used", "OK")
    
    
    # QUERIES
    
    # Get data type
    def get_type(self) -> Type[Any]:
        return self.__type

    # Get data state
    def get_state(self) -> DataSource.State:
        return self.__state

    # Get data
    # PRE: data state is not `NONE`
    @status("OK", "NO_DATA")
    def get(self) -> Any:
        if self.__state == DataSource.State.NONE:
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
    def get_input(self, id: str) -> DataDest[Any]:
        assert False

    # Get output slot
    # PRE: `id` is valid output slot ID
    @abstractmethod
    @status("OK", "INVALID_ID")
    def get_output(self, id: str) -> DataSource[Any]:
        assert False


class Calculator(Procedure):
    pass


def _type_fits(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False
