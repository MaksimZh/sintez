from abc import ABC, abstractmethod
from typing import Any, TypeVar, Callable, get_origin, get_args
from inspect import getfullargspec

from tools import Status, status


T = TypeVar("T")
Func = Callable[..., Any]


# Base class for solvers that are procedures with state
# CONTAINS:
#   - input values
#   - output values
class Solver(Status):
    
    # COMMANDS

    # Set input value
    # PRE: `id` is valid input id
    # PRE: `value` is acceptable for this id
    # POST: input `id` is equal to `value`
    @abstractmethod
    @status("OK", "INVALID_ID", "INVALID_VALUE")
    def put(self, id: str, value: Any) -> None:
        assert False

    # Run solver
    # PRE: input values are set and acceptable
    # PRE: solution can be found for current input
    # POST: output values are set
    @abstractmethod
    @status("OK", "INVALID_INPUT", "INTERNAL_ERROR")
    def run(self) -> None:
        assert False


    # QUERIES
    
    # Get input value ids and types
    @abstractmethod
    def get_input_spec(self) -> dict[str, type]:
        assert False

    # Get output value ids and types
    @abstractmethod
    def get_output_spec(self) -> dict[str, type]:
        assert False

    # Check if input or output value is set
    # PRE: `id` is valid input or output name
    @abstractmethod
    @status("OK", "INVALID_ID")
    def has_value(self, id: str) -> bool:
        assert False
    
    # Get input or output value
    # PRE: `id` is valid input or output name
    @abstractmethod
    @status("OK", "INVALID_ID")
    def get(self, id: str) -> Any:
        assert False


# Factory for solvers
# CONTAINS:
#   - input ids
#   - input types
#   - output ids
#   - output types
class SolverFactory(ABC):

    # Create solver
    # POST: `Solver` inputs and outputs have no values
    @abstractmethod
    def create(self) -> Solver:
        assert False

    # Get solver input value ids and types
    @abstractmethod
    def get_input_spec(self) -> dict[str, type]:
        assert False

    # Get solver output value ids and types
    @abstractmethod
    def get_output_spec(self) -> dict[str, type]:
        assert False


# Solver wrapping function
class WrapperSolver(Solver):

    __func: Func
    __input_spec: dict[str, type]
    __output_spec: dict[str, type]
    __inputs: dict[str, Any]


    # CONSTRUCTOR
    def __init__(self, func: Func, 
            input_spec: dict[str, type], output_spec: dict[str, type]) -> None:
        super().__init__()
        self.__func = func
        self.__input_spec = input_spec
        self.__output_spec = output_spec

    
    # COMMANDS

    # Set input value
    # PRE: `id` is valid input id
    # PRE: `value` is acceptable for this id
    # POST: input `id` is equal to `value`
    @status("OK", "INVALID_ID", "INVALID_VALUE")
    def put(self, id: str, value: Any) -> None:
        if not id in self.__input_spec:
            self._set_status("put", "INVALID_ID")
            return
        if not _type_fits(type(value), self.__input_spec[id]):
            self._set_status("put", "INVALID_VALUE")
            return
        self._set_status("put", "OK")

    # Run solver
    # PRE: input values are set and acceptable
    # PRE: solution can be found for current input
    # POST: output values are set
    @status("OK", "INVALID_INPUT", "INTERNAL_ERROR")
    def run(self) -> None:
        self._set_status("run", "OK")  


    # QUERIES
    
    # Get input value ids and types
    def get_input_spec(self) -> dict[str, type]:
        return self.__input_spec

    # Get output value ids and types
    def get_output_spec(self) -> dict[str, type]:
        return self.__output_spec

    # Check if input or output value is set
    # PRE: `id` is valid input or output name
    @status("OK", "INVALID_ID")
    def has_value(self, id: str) -> bool:
        assert False
    
    # Get input or output value
    # PRE: `id` is valid input or output name
    @status("OK", "INVALID_ID")
    def get(self, id: str) -> Any:
        assert False


# Factory for solver wrapping function
# CONTAINS:
#   - input ids
#   - input types
#   - output ids
#   - output types
class Wrapper(SolverFactory):

    __func: Func
    __input_spec: dict[str, type]
    __output_spec: dict[str, type]


    # CONSTRUCTOR
    # PRE: `func` has argument and return type annotations
    # PRE: length of `output_names` matches function return type tuple length
    #      single value is treated as tuple of length 1
    # POST: input ids are `func` argument names
    # POST: input types are `func` argument types
    # POST: output ids are `output_ids`
    # POST: output types are return tuple type elements
    def __init__(self, func: Func, output_ids: list[str]) -> None:
        super().__init__()
        self.__func = func
        arg_spec = getfullargspec(func)
        self.__input_spec = dict()
        self.__output_spec = dict()
        for id in arg_spec.args:
            self.__input_spec[id] = arg_spec.annotations[id]
        if "return" not in arg_spec.annotations:
            assert len(output_ids) == 0
            return
        return_type = arg_spec.annotations["return"]
        if get_origin(return_type) is not tuple:
            assert len(output_ids) == 1
            self.__output_spec[output_ids[0]] = return_type
            return
        output_types = get_args(return_type)
        for i in range(len(output_ids)):
            self.__output_spec[output_ids[i]] = output_types[i]

    # Create solver
    # POST: `Solver` inputs and outputs have no values
    def create(self) -> Solver:
        return WrapperSolver(self.__func, self.__input_spec, self.__output_spec)

    # Get solver input value ids and types
    def get_input_spec(self) -> dict[str, type]:
        return self.__input_spec

    # Get solver output value ids and types
    def get_output_spec(self) -> dict[str, type]:
        return self.__output_spec


def _type_fits(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False
