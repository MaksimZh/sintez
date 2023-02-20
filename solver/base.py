from abc import ABC, abstractmethod
from typing import Any

from tools import Status, status


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
    # PRE: there is value at `id`
    @abstractmethod
    @status("OK", "INVALID_ID", "NO_VALUE")
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


def is_subtype(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False
