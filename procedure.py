from typing import TypeVar, Type, Any, Generic, get_origin, get_args
from abc import abstractmethod
from tools import Status, status, StatusMeta


T = TypeVar("T")

# Interface for data input
# Generic argument is used in `Calculator`
# CONTAINS:
#   - data
#   - data type
#   - data state (has data or not)
class Input(Generic[T], Status):
    
    # QUERIES

    # Get data type
    @abstractmethod
    def get_type(self) -> Type[T]:
        assert False

    # Get data state
    @abstractmethod
    def has_data(self) -> bool:
        assert False

    # Get data
    # PRE: has data
    @abstractmethod
    @status("OK", "NO_DATA")
    def get(self) -> T:
        assert False


# Interface for data output
# Generic argument is used in `Calculator`
# CONTAINS:
#   - data
#   - data type
#   - data state (has data or not)
class Output(Generic[T], Status):

    # COMMANDS

    # Set data
    # PRE: `value` type fits data type
    # POST: data is `value`
    @abstractmethod
    @status("OK", "INVALID_TYPE")
    def set(self, value: T) -> None:
        assert False

    # Delete data
    # POST: no data
    @abstractmethod
    def clear(self) -> None:
        assert False

    
    # QUERIES
    
    # Get data type
    @abstractmethod
    def get_type(self) -> Type[T]:
        assert False


DataSource = Input[Any]
DataDest = Output[Any]


# Slot containing data
# CONTAINS:
#   - data
#   - data type
#   - data state (has data or not)
class Slot(DataSource, DataDest):
    
    __type: type
    __value: Any
    __has_data: bool
    
    
    # CONSTRUCTOR
    # POST: data type is `data_type`
    # POST: no data
    def __init__(self, data_type: type) -> None:
        super().__init__()
        self.__type = data_type
        self.__has_data = False

    
    # COMMANDS

    # Set data
    # PRE: `value` type fits data type
    # POST: data is `value`
    @status("OK", "INVALID_TYPE")
    def set(self, value: Any) -> None:
        if not _type_fits(type(value), self.__type):
            self._set_status("set", "INVALID_TYPE")
            return
        self._set_status("set", "OK")
        self.__has_data = True
        self.__value = value

    # Delete data
    # POST: no data
    def clear(self) -> None:
        self.__has_data = False
    
    
    # QUERIES
    
    # Get data type
    def get_type(self) -> Type[Any]:
        return self.__type

    # Get data state
    def has_data(self) -> bool:
        return self.__has_data

    # Get data
    # PRE: has data
    @status("OK", "NO_DATA")
    def get(self) -> Any:
        if not self.__has_data:
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
    def get_input(self, id: str) -> DataDest:
        assert False

    # Get output slot
    # PRE: `id` is valid output slot ID
    @abstractmethod
    @status("OK", "INVALID_ID")
    def get_output(self, id: str) -> DataSource:
        assert False


class CalculatorMeta(StatusMeta):
    
    def __new__(cls, class_name: str, bases: tuple[type, ...],
            namespace: dict[str, Any], **kwargs: Any) -> type:
        namespace["__inputs"] = cls.__get_fields(class_name, namespace, Input)
        namespace["__outputs"] = cls.__get_fields(class_name, namespace, Output)
        return super().__new__(cls, class_name, bases, namespace, **kwargs)

    @staticmethod
    def __get_fields(class_name: str, namespace: dict[str, Any],
            required_type: type) -> list[tuple[str, str, type]]:
        if "__annotations__" not in namespace:
            return list()
        fields = list[tuple[str, str, type]]()
        private_prefix = f"_{class_name}__"
        for field_name, field_type in namespace["__annotations__"].items():
            if get_origin(field_type) is not required_type:
                continue
            if field_name.startswith(private_prefix):
                slot_name = field_name[len(private_prefix):]
            elif field_name.startswith("_"):
                slot_name = field_name[1:]
            else:
                slot_name = field_name
            field_args = get_args(field_type)
            assert(len(field_args) == 1)
            data_type = field_args[0]
            fields.append((slot_name, field_name, data_type))
        return fields


# Procedure that automatically detects input and output slots from fields
# and performs calculations using custom algorithm
class Calculator(Procedure, metaclass=CalculatorMeta):

    __input_fields: dict[str, str]
    __output_fields: dict[str, str]

    # CONSTRUCTOR
    # POST: all `Input` and `Output` fields contain slots of specified types
    def __init__(self) -> None:
        super().__init__()
        self.__input_fields = dict()
        self.__output_fields = dict()
        for slot_name, field_name, data_type in getattr(self, "__inputs"):
            setattr(self, field_name, Slot(data_type))
            self.__input_fields[slot_name] = field_name
        for slot_name, field_name, data_type in getattr(self, "__outputs"):
            setattr(self, field_name, Slot(data_type))
            self.__output_fields[slot_name] = field_name
    
    
    # COMMANDS

    # Run calculations
    # Checks inputs then calls `calculate` method and then checks outputs
    # PRE: all inputs have data
    # PRE: input data lead to successfull calculation
    # POST: all outputs have data
    @status("OK", "INVALID_INPUT", "INTERNAL_ERROR")
    def run(self) -> None:
        for field_name in self.__input_fields.values():
            slot: Slot = getattr(self, field_name)
            if not slot.has_data():
                self._set_status("run", "INVALID_INPUT")
                return
        self.calculate()
        if not self.is_status("calculate", "OK"):
            self._set_status("run", "INTERNAL_ERROR")
            return
        for field_name in self.__output_fields.values():
            slot: Slot = getattr(self, field_name)
            if not slot.has_data():
                self._set_status("run", "INTERNAL_ERROR")
                return
        self._set_status("run", "OK")

    # Run calculations
    # To be implemented in child classes
    # PRE: input data lead to successfull calculation
    # POST: all outputs have data
    @abstractmethod
    @status("OK", "ERROR")
    def calculate(self) -> None:
        assert False


    # QUERIES

    # Get IDs of input slots
    def get_input_ids(self) -> set[str]:
        return set(self.__input_fields.keys())

    # Get IDs of output slots
    def get_output_ids(self) -> set[str]:
        return set(self.__output_fields.keys())

    # Get input slot
    # PRE: `id` is valid input slot ID
    @status("OK", "INVALID_ID")
    def get_input(self, id: str) -> DataDest:
        if id not in self.__input_fields:
            self._set_status("get_input", "INVALID_ID")
            return Slot(object)
        self._set_status("get_input", "OK")
        return getattr(self, self.__input_fields[id])

    # Get output slot
    # PRE: `id` is valid output slot ID
    @status("OK", "INVALID_ID")
    def get_output(self, id: str) -> DataSource:
        if id not in self.__output_fields:
            self._set_status("get_output", "INVALID_ID")
            return Slot(object)
        self._set_status("get_output", "OK")
        return getattr(self, self.__output_fields[id])


def _type_fits(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False
