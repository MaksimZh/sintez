from typing import Any
from abc import abstractmethod
from tools import Status, status


# Basic calculation logic unit
# CONTAINS:
#   - input slots (names and types)
#   - output slots (names and types)
#   - input values
#   - output values
#   - input status (changed after last run or not)
class Procedure(Status):
    
    # COMMANDS

    # Set input value
    # PRE: `slot` is valid input slot name
    # PRE: type of `value` is compatible with slot
    # PRE: `value` is acceptable for the procedure
    # POST: input value in slot `slot` is set to `value`
    @abstractmethod
    @status("OK", "INVALID_SLOT", "INVALID_TYPE", "INVALID_VALUE")
    def set(self, slot: str, value: Any) -> None:
        assert False

    # Run procedure
    # PRE: input values are set and valid
    # POST: output values are set
    # POST: input values status set to unchanged
    @abstractmethod
    @status("OK", "INVALID_INPUT")
    def run(self) -> None:
        assert False


    # QUERIES

    # Get output value
    # PRE: slot is valid output slot name
    # PRE: run was successful after last input change
    @abstractmethod
    @status("OK", "INVALID_SLOT", "NEEDS_RUN")
    def get(self, slot: str) -> Any:
        assert False
