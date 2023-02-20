from typing import Any, Callable, get_origin, get_args
from inspect import getfullargspec

from tools import status
from solver.base import Solver, SolverFactory, is_subtype


Func = Callable[..., Any]


# Solver wrapping function
class WrapperSolver(Solver):

    __spec: "FuncSpec"
    __inputs: dict[str, Any]
    __outputs: dict[str, Any]


    # CONSTRUCTOR
    def __init__(self, spec: "FuncSpec") -> None:
        super().__init__()
        self.__spec = spec
        self.__inputs = dict()
        self.__outputs = dict()

    
    # COMMANDS

    # Set input value
    # PRE: `id` is valid input id
    # PRE: `value` is acceptable for this id
    # POST: input `id` is equal to `value`
    @status("OK", "INVALID_ID", "INVALID_VALUE")
    def put(self, id: str, value: Any) -> None:
        if not id in self.__spec.get_input_spec():
            self._set_status("put", "INVALID_ID")
            return
        if not is_subtype(type(value), self.__spec.get_input_spec()[id]):
            self._set_status("put", "INVALID_VALUE")
            return
        self.__inputs[id] = value
        self._set_status("put", "OK")

    # Run solver
    # PRE: input values are set and acceptable
    # PRE: solution can be found for current input
    # POST: output values are set
    @status("OK", "INVALID_INPUT", "INTERNAL_ERROR")
    def run(self) -> None:
        args = list[Any]()
        for id in self.__spec.get_input_ids():
            if id not in self.__inputs:
                self._set_status("run", "INVALID_INPUT")
                return
            args.append(self.__inputs[id])
        try:
            result = self.__spec.get_func()(*args)
        except:
            self._set_status("run", "INTERNAL_ERROR")
            return
        output_ids = self.__spec.get_output_ids()
        output_spec = self.__spec.get_output_spec()
        if len(output_ids) == 1:
            result = tuple(result,)
        for i in range(len(output_ids)):
            value = result[i]
            id = output_ids[i]
            if not is_subtype(type(value), output_spec[id]):
                self._set_status("run", "INTERNAL_ERROR")
                return
            self.__outputs[id] = value
        self._set_status("run", "OK")  


    # QUERIES
    
    # Get input value ids and types
    def get_input_spec(self) -> dict[str, type]:
        return self.__spec.get_input_spec()

    # Get output value ids and types
    def get_output_spec(self) -> dict[str, type]:
        return self.__spec.get_output_spec()

    # Check if input or output value is set
    # PRE: `id` is valid input or output name
    @status("OK", "INVALID_ID")
    def has_value(self, id: str) -> bool:
        if id in self.__spec.get_input_ids():
            self._set_status("has_value", "OK")
            return id in self.__inputs
        if id in self.__spec.get_output_ids():
            self._set_status("has_value", "OK")
            return id in self.__outputs
        self._set_status("has_value", "INVALID_ID")
        return False

    # Get input or output value
    # PRE: `id` is valid input or output name
    # PRE: there is value at `id`
    @status("OK", "INVALID_ID", "NO_VALUE")
    def get(self, id: str) -> Any:
        if id in self.__spec.get_input_ids():
            return self.__get_input(id)
        if id in self.__spec.get_output_ids():
            return self.__get_output(id)
        self._set_status("get", "INVALID_ID")
        return None

    def __get_input(self, id: str) -> Any:
        if id not in self.__inputs:
            self._set_status("get", "NO_VALUE")
            return None
        self._set_status("get", "OK")
        return self.__inputs[id]

    def __get_output(self, id: str) -> Any:
        if id not in self.__outputs:
            self._set_status("get", "NO_VALUE")
            return None
        self._set_status("get", "OK")
        return self.__outputs[id]


# Factory for solver wrapping function
# CONTAINS:
#   - input ids
#   - input types
#   - output ids
#   - output types
class Wrapper(SolverFactory):

    __spec: "FuncSpec"


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
        self.__spec = FuncSpec(func, output_ids)

    # Create solver
    # POST: `Solver` inputs and outputs have no values
    def create(self) -> Solver:
        return WrapperSolver(self.__spec)

    # Get solver input value ids and types
    def get_input_spec(self) -> dict[str, type]:
        return self.__spec.get_input_spec()

    # Get solver output value ids and types
    def get_output_spec(self) -> dict[str, type]:
        return self.__spec.get_output_spec()


class FuncSpec:

    __func: Func
    __input_ids: list[str]
    __output_ids: list[str]
    __input_spec: dict[str, type]
    __output_spec: dict[str, type]

    def __init__(self, func: Func, output_ids: list[str]) -> None:
        self.__func = func
        arg_spec = getfullargspec(func)
        self.__input_ids = list()
        self.__output_ids = output_ids
        self.__input_spec = dict()
        self.__output_spec = dict()
        for id in arg_spec.args:
            self.__input_ids.append(id)
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

    def get_func(self) -> Func:
        return self.__func

    def get_input_ids(self) -> list[str]:
        return self.__input_ids
    
    def get_output_ids(self) -> list[str]:
        return self.__output_ids

    def get_input_spec(self) -> dict[str, type]:
        return self.__input_spec
    
    def get_output_spec(self) -> dict[str, type]:
        return self.__output_spec
