from abc import abstractmethod
from typing import Any, TypeVar, Type, Generic, get_origin, get_args

from tools import Status, status, StatusMeta
from solver.base import Solver, is_subtype


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
    def has_value(self) -> bool:
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
class Output(Generic[T], Status):

    # COMMANDS

    # Set data
    # PRE: `value` type fits data type
    # POST: data is `value`
    @abstractmethod
    @status("OK", "INVALID_VALUE")
    def put(self, value: T) -> None:
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
    @status("OK", "INVALID_VALUE")
    def put(self, value: Any) -> None:
        if not is_subtype(type(value), self.__type):
            self._set_status("put", "INVALID_VALUE")
            return
        self._set_status("put", "OK")
        self.__has_data = True
        self.__value = value


    # QUERIES
    
    # Get data type
    def get_type(self) -> Type[Any]:
        return self.__type

    # Get data state
    def has_value(self) -> bool:
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


class CalculatorMeta(StatusMeta):
    
    def __new__(cls, class_name: str, bases: tuple[type, ...],
            namespace: dict[str, Any], **kwargs: Any) -> type:
        inputs = cls.__get_fields(class_name, namespace, Input)
        outputs = cls.__get_fields(class_name, namespace, Output)
        namespace["__input_fields"] = dict([(v[0], v[1]) for v in inputs])
        namespace["__output_fields"] = dict([(v[0], v[1]) for v in outputs])
        namespace["__input_types"] = dict([(v[0], v[2]) for v in inputs])
        namespace["__output_types"] = dict([(v[0], v[2]) for v in outputs])
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
                id = field_name[len(private_prefix):]
            elif field_name.startswith("_"):
                id = field_name[1:]
            else:
                id = field_name
            field_args = get_args(field_type)
            assert(len(field_args) == 1)
            data_type = field_args[0]
            fields.append((id, field_name, data_type))
        return fields


class Calculator(Solver, metaclass=CalculatorMeta):

    # CONSTRUCTOR
    # POST: all `Input` and `Output` fields contain slots of specified types
    def __init__(self) -> None:
        super().__init__()
        self.__make_slots(
            getattr(self, "__input_fields"),
            getattr(self, "__input_types"))
        self.__make_slots(
            getattr(self, "__output_fields"),
            getattr(self, "__output_types"))

    def __make_slots(self, fields: dict[str, str], types: dict[str, type]):
        assert fields.keys() == types.keys()
        for id in fields.keys():
            setattr(self, fields[id], Slot(types[id]))


    # COMMANDS

    # Set input value
    # PRE: `id` is valid input id
    # PRE: `value` is acceptable for this id
    # POST: input `id` is equal to `value`
    @status("OK", "INVALID_ID", "INVALID_VALUE")
    def put(self, id: str, value: Any) -> None:
        input_fields: dict[str, str] = getattr(self, "__input_fields")
        if id not in input_fields:
            self._set_status("put", "INVALID_ID")
            return
        input: Slot = getattr(self, input_fields[id])
        input.put(value)
        if not input.is_status("put", "OK"):
            self._set_status("put", "INVALID_VALUE")
            return
        self._set_status("put", "OK")
        return


    # Run solver
    # PRE: input values are set and acceptable
    # PRE: solution can be found for current input
    # POST: output values are set
    @status("OK", "INVALID_INPUT", "INTERNAL_ERROR")
    def run(self) -> None:
        for field_name in getattr(self, "__input_fields").values():
            slot: Slot = getattr(self, field_name)
            if not slot.has_value():
                self._set_status("run", "INVALID_INPUT")
                return
        self.calculate()
        if not self.is_status("calculate", "OK"):
            self._set_status("run", "INTERNAL_ERROR")
            return
        for field_name in getattr(self, "__output_fields").values():
            slot: Slot = getattr(self, field_name)
            if not slot.has_value():
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
    
    # Get input value ids and types
    def get_input_spec(self) -> dict[str, type]:
        return getattr(self, "__input_types")

    # Get output value ids and types
    def get_output_spec(self) -> dict[str, type]:
        return getattr(self, "__output_types")

    # Check if input or output value is set
    # PRE: `id` is valid input or output name
    @status("OK", "INVALID_ID")
    def has_value(self, id: str) -> bool:
        input_fields: dict[str, str] = getattr(self, "__input_fields")
        if id in input_fields:
            self._set_status("has_value", "OK")
            return getattr(self, input_fields[id]).has_value()
        output_fields: dict[str, str] = getattr(self, "__output_fields")
        if id in output_fields:
            self._set_status("has_value", "OK")
            return getattr(self, output_fields[id]).has_value()
        self._set_status("has_value", "INVALID_ID")
        return False
    
    # Get input or output value
    # PRE: `id` is valid input or output name
    # PRE: there is value at `id`
    @status("OK", "INVALID_ID", "NO_VALUE")
    def get(self, id: str) -> Any:
        input_fields: dict[str, str] = getattr(self, "__input_fields")
        if id in input_fields:
            return self.__get_value(getattr(self, input_fields[id]))
        output_fields: dict[str, str] = getattr(self, "__output_fields")
        if id in output_fields:
            return self.__get_value(getattr(self, output_fields[id]))
        self._set_status("get", "INVALID_ID")
        return None
    
    def __get_value(self, slot: Slot) -> Any:
        if not slot.has_value():
            self._set_status("get", "NO_VALUE")
            return None
        self._set_status("get", "OK")
        return slot.get()
