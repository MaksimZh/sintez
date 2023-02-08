from typing import TypeVar, Type, Any, Generic
from abc import abstractmethod
from enum import Enum, auto
from tools import Status, status
from procedures import _type_fits

T = TypeVar("T")


class DataSource(Generic[T], Status):
    
    @abstractmethod
    def get_type(self) -> Type[T]:
        assert False

    class State(Enum):
        NONE = auto(),
        NEW = auto(),
        USED = auto(),

    @abstractmethod
    def get_state(self) -> State:
        assert False

    @abstractmethod
    @status("OK", "NO_DATA")
    def get(self) -> T:
        assert False
        

class DataDest(Generic[T], Status):
    
    @abstractmethod
    def get_type(self) -> Type[T]:
        assert False

    @abstractmethod
    @status("OK", "INVALID_TYPE")
    def set(self, value: T) -> None:
        assert False


class DataSlot(DataSource[Any], DataDest[Any]):
    
    __type: type
    __value: Any
    __state: DataSource.State

    def __init__(self, data_type: type) -> None:
        super().__init__()
        self.__type = data_type
        self.__state = self.State.NONE
    
    def get_type(self) -> Type[Any]:
        return self.__type

    def get_state(self) -> DataSource.State:
        return self.__state

    @status("OK", "NO_DATA")
    def get(self) -> Any:
        if self.__state == DataSource.State.NONE:
            self._set_status("get", "NO_DATA")
            return None
        self._set_status("get", "OK")
        self.__state = self.State.USED
        return self.__value

    @status("OK", "INVALID_TYPE")
    def set(self, value: Any) -> None:
        if not _type_fits(type(value), self.__type):
            self._set_status("set", "INVALID_TYPE")
            return
        self._set_status("set", "OK")
        self.__state = self.State.NEW
        self.__value = value


class Procedure(Status):

    @classmethod
    @abstractmethod
    def get_input_spec(cls) -> dict[str, type]:
        assert False

    @abstractmethod
    def get_inputs_id(self) -> set[str]:
        assert False

    @abstractmethod
    def get_outputs_id(self) -> set[str]:
        assert False

    @abstractmethod
    @status("OK", "INVALID_ID")
    def get_input(self, id: str) -> DataDest[Any]:
        assert False

    @abstractmethod
    @status("OK", "INVALID_ID")
    def get_output(self, id: str) -> DataSource[Any]:
        assert False

    @abstractmethod
    @status("OK", "INVALID_INPUT", "INTERNAL_ERROR")
    def run(self) -> None:
        assert False


class Foo:
    
    __left: DataSource[int]
    __right: DataSource[int]
    __quotient: DataDest[int]
    __remainder: DataDest[int]

    def __init__(self) -> None:
        self.__left = DataSlot(int)
        self.__right = DataSlot(int)
        self.__quotient = DataSlot(int)
        self.__remainder = DataSlot(int)
