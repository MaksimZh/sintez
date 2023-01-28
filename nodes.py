from typing import Any, Optional, final, Type
from abc import abstractmethod
from tools import Status, status, StatusMeta

# Nodes implement the calculation scheme logic.
#
# DataNode can be linked only to ProcNodes and vice versa.
# All links have one and only one direction, no loops allowed.
# The basic concepts of calculation are invalidation and validation.
# Data change invalidates all succeeding nodes.
# Procedure validation validates all its output nodes.
# When node is invalidated it invalidates all succeeding nodes.
# When node is validated it requests validation of all preceding nodes.

# Interface of data input for procedures.
#
# Contains:
#     - output procedures
#     - input procedure
#     - data type
#     - data status (valid or not)
#     - data (if valid, read only)
#
class InputData(Status):
    
    # COMMANDS
    
    # Add output procedure
    # PRE: `output` is not in this data input or outputs
    # POST: `output` is in outputs
    @abstractmethod
    @status("OK", "ALREADY_LINKED")
    def add_output(self, output: "OutputProc") -> None:
        assert False

    # Make sure data is valid
    # PRE: data is valid or input procedure can be validated
    # POST: data is valid
    @abstractmethod
    @status("OK", "NO_INPUT", "INPUT_VALIDATION_FAIL")
    def validate(self, output: "OutputProc") -> None:
        assert False

    
    # QUERIES

    # Get data type
    @abstractmethod
    def get_type(self) -> type:
        assert False

    # Check if data is valid
    @abstractmethod
    def is_valid(self) -> bool:
        assert False

    # Get data
    # PRE: data is valid
    @abstractmethod
    @status("OK", "INVALID_DATA")
    def get(self) -> Any:
        assert False


# Interface of data output for procedures.
#
# Contains:
#     - data type
#     - data (write only)
#
class OutputData(Status):

    # COMMANDS

    # Set data
    # PRE: `value` type can be implicitly converted to data type
    # POST: data is set to `value`
    @abstractmethod
    @status("OK", "INCOMPATIBLE_TYPE")
    def put(self, value: Any) -> None:
        assert False

    # Inform about input invalidation
    @abstractmethod
    def invalidate(self) -> None:
        assert False


    # QUERIES

    # Get data type
    @abstractmethod
    def get_type(self) -> type:
        assert False


# Interface of data input for data nodes.
#
# Contains:
#     - output data nodes at named slots
#     - input data nodes
#     - procedure
#
class InputProc(Status):
    
    # Add output data node
    # PRE: `slot` exists and not occupied
    # PRE: `output` is not in inputs or outputs
    # PRE: `output` type is compatible with `slot`
    # POST: `output` is linked to this data input as `slot`
    @abstractmethod
    @status("OK",
        "INVALID_SLOT_NAME",
        "SLOT_OCCUPIED",
        "ALREADY_LINKED",
        "INCOMPATIBLE_TYPE")
    def add_output(self, slot: str, output: OutputData) -> None:
        assert False
        
    # Request validation of all output data
    # PRE: input data can be validated
    # PRE: input data have correct values
    # POST: send data to all outputs
    @abstractmethod
    @status("OK",
        "INPUT_VALIDATION_FAIL",
        "INVALID_INPUT_VALUE",
        "INVALID_PROCEDURE")
    def validate(self) -> None:
        assert False


# Interface of data outputs for data nodes.
#
# Contains:
#     - linked inputs
#
class OutputProc(Status):

    # Inform about input invalidation
    # PRE: `input` is in procedure inputs
    @abstractmethod
    @status("OK", "NOT_INPUT")
    def invalidate(self, input: InputData) -> None:
        assert False


# Implements data node part of calculation scheme logic.
# Can have only one (optional) input procedure.
# So there is only one component responsible for value update.
#
# Note that value must be validated before `get` query is used.
#
# Contains:
#     - input procedure node (optional)
#     - output procedure nodes (any number)
#     - data type
#     - data status (valid or not)
#     - data (if valid)
#
@final
class DataNode(InputData, OutputData):

    __input: Optional[InputProc]
    __outputs: set[OutputProc]
    __type: type
    __data: Any
    __is_valid: bool

    # CONSTRUCTOR
    # PRE: `input` is `None` or procedure node that accepts connection
    #      of data with `data_type` type to output `slot`
    # POST: input procedure node is set to `input`
    # POST: if `input` is not None add this node to `input` output slot `slot`
    # POST: no output procedure nodes
    # POST: data type is `data_type`
    # POST: data is invalid
    @status("OK",
        "INVALID_SLOT_NAME",
        "SLOT_OCCUPIED",
        "ALREADY_LINKED",
        "INCOMPATIBLE_TYPE",
        name="init")
    def __init__(self,
            data_type: type,
            input: Optional[InputProc] = None,
            slot: Optional[str] = None):
        super().__init__()
        self.__type = data_type
        self.__is_valid = False
        self.__input = None
        self.__outputs = set()
        if input is None:
            self._set_status("init", "OK")
            return
        input.add_output(self, slot)
        if not input.is_status("add_output", "OK"):
            self._set_status("init", input.get_status("add_output"))
            return
        self.__input = input
        self._set_status("init", "OK")


    # COMMANDS
    
    # Add output procedure
    # PRE: `output` is not in input or outputs
    # POST: `output` is in outputs
    @status()
    def add_output(self, output: "OutputProc") -> None:
        if output is self.__input or output in self.__outputs:
            self._set_status("add_output", "ALREADY_LINKED")
            return
        self.__outputs.add(output)
        self._set_status("add_output", "OK")

    # Set data
    # PRE: `value` type can be implicitly converted to data type
    # POST: data is valid
    # POST: data is `value`
    # POST: if data was valid then all outputs are invalidated
    @status()
    def put(self, value: Any) -> None:
        if not _type_fits(type(value), self.__type):
            self._set_status("put", "INCOMPATIBLE_TYPE")
            return
        self.__data = value
        self._set_status("put", "OK")
        if not self.is_valid():
            self.__is_valid = True
            return
        for output in self.__outputs:
            output.invalidate(self)

    # Inform about input invalidation
    # POST: data is invalid
    # POST: if data was valid then all outputs are invalidated
    def invalidate(self) -> None:
        if not self.is_valid():
            return
        self.__is_valid = False
        for output in self.__outputs:
            output.invalidate(self)

    # Make sure data is valid
    # PRE: data is valid or input procedure can be validated
    # POST: if data was invalid then input is validated
    # POST: data is valid
    @status()
    def validate(self) -> None:
        if self.is_valid():
            self._set_status("validate", "OK")
            return
        if self.__input is None:
            self._set_status("validate", "NO_INPUT")
            return
        self.__input.validate()
        if not self.__input.is_status("validate", "OK"):
            self._set_status("validate", "INPUT_VALIDATION_FAIL")
            return
        self._set_status("validate", "OK")


    # QUERIES

    # Get data type
    def get_type(self) -> type:
        return self.__type

    # Check if data is valid
    def is_valid(self) -> bool:
        return self.__is_valid

    # Get data
    # PRE: data is valid
    @status("OK", "INVALID_DATA")
    def get(self) -> Any:
        if not self.is_valid():
            self._set_status("get", "INVALID_DATA")
            return None
        self._set_status("get", "OK")
        return self.__data


# Base class for the internal procedure of ProcedureNode
# 
# When the user gets any output value it must be up to date with input values.
# Procedure implementation must take care of the method statuses.
#
# Types of the input data are checked before procedure creation.
# Override `get_input_types` class method to provide infomation for type check.
# Output types are requested once from created class instance
# with `get_output_types` query.
#
# These two methods declares procedure IO specification:
# Procedure must accept inputs of specified types at specified slots.
# Procedure must provide outputs of specified types at specified slots.
#
# Contains:
#     - named and typed input data
#     - named and typed output data 
#
class Procedure(Status):

    # CLASS QUERIES

    # Get names and types of input data slots
    @classmethod
    @abstractmethod
    def get_input_types(cls) -> dict[str, type]:
        assert False

    # Create procedure for given input types that are subtypes of the slot types
    @classmethod
    @abstractmethod
    def create(cls, input_types: dict[str, type]) -> "Procedure":
        assert False

    
    # COMMANDS
    
    # Set input value
    # PRE: `slot` is input slot
    # PRE: `value` type is compatible
    # PRE: `value` is valid (fits procedure logic)
    # POST: input data in `slot` is set to `value`
    @abstractmethod
    @status("OK", "INVALID_NAME", "INCOMPATIBLE_TYPE", "INVALID_VALUE")
    def put(self, slot: str, value: Any) -> None:
        assert False


    # QUERIES

    # Get names and types of outputs
    @abstractmethod
    def get_output_types(self) -> dict[str, type]:
        assert False

    # get value
    # PRE: `slot` is output slot
    # PRE: there is enough input data for calculation
    @abstractmethod
    @status("OK", "INVALID_NAME", "INCOMPLETE_INPUT")
    def get(self, slot: str) -> Any:
        assert False


# Implements procedure node part of calculation scheme logic.
#
# Contains:
#     - input data nodes (any number)
#     - output data nodes (any number)
#     - procedure
#     - input data markers (new or used)
#
@final
class ProcNode(InputProc, OutputProc):

    __proc: Procedure
    __output_types: dict[str, type]
    __inputs: dict[str, InputData]
    __outputs: dict[str, OutputData]
    __new_inputs: set[InputData]


    # CONSTRUCTOR
    # PRE: `inputs` fit procedure inputs
    # POST: `inputs` are connected to input slots
    # POST: no output nodes
    # POST: procedure created
    # POST: all inputs are marked as new
    # POST: this node is added as output to all inputs
    @status(
        "OK",
        "INCOMPLETE_INPUT",
        "INCOMPATIBLE_INPUT_SLOTS",
        "INCOMPATIBLE_INPUT_TYPES",
        name="init")
    def __init__(self, proc_type: Type[Procedure],
            inputs: dict[str, InputData]) -> None:
        super().__init__()
        self.__inputs = dict()
        self.__outputs = dict()
        proc_input_types = proc_type.get_input_types()
        if proc_input_types.keys() > inputs.keys():
            self._set_status("init", "INCOMPLETE_INPUT")
            return
        if proc_input_types.keys() != inputs.keys():
            self._set_status("init", "INCOMPATIBLE_INPUT_SLOTS")
            return
        for slot, input in inputs.items():
            if not _type_fits(input.get_type(), proc_input_types[slot]):
                self._set_status("init", "INCOMPATIBLE_INPUT_TYPES")
                return
        for slot, input in inputs.items():
            self.__inputs[slot] = input
            input.add_output(self)
            assert(input.is_status("add_output", "OK"))
        self.__new_inputs = set(self.__inputs.values())
        self.__proc = proc_type.create(proc_input_types)
        self.__output_types = self.__proc.get_output_types()
        self._set_status("init", "OK")

    
    # COMMANDS
    
    # Add output data node
    # PRE: output `slot` for procedure exists and not occupied
    # PRE: `output` is not in this node inputs or outputs
    # PRE: `output` type is compatible with `slot`
    # POST: `output` is linked to this node outputs as `slot`
    @status()
    def add_output(self, slot: str, output: OutputData) -> None:
        if not slot in self.__output_types:
            self._set_status("add_output", "INVALID_SLOT_NAME")
            return
        if slot in self.__outputs:
            self._set_status("add_output", "SLOT_OCCUPIED")
            return
        if output in self.__inputs.values():
            self._set_status("add_output", "ALREADY_LINKED")
            return
        if output in self.__outputs.values():
            self._set_status("add_output", "ALREADY_LINKED")
            return
        if not _type_fits(self.__output_types[slot], output.get_type()):
            self._set_status("add_output", "INCOMPATIBLE_TYPE")
            return
        self.__outputs[slot] = output
        self._set_status("add_output", "OK")

    # Inform about input invalidation
    # PRE: `input` is in procedure inputs
    # POST: `input` is marked as new
    # POST: outputs are invalidated
    @status()
    def invalidate(self, input: InputData) -> None:
        if input not in self.__inputs.values():
            self._set_status("invalidate", "NOT_INPUT")
            return
        self.__new_inputs.add(input)
        self._set_status("invalidate", "OK")
        for output in self.__outputs.values():
            output.invalidate()

    # Request validation of all output data
    # PRE: inputs can be validated
    # PRE: input data are correct for procedure
    # PRE: procedure follows its own IO specification
    # POST: all inputs are validated
    # POST: data requested from all new inputs and sent to procedure
    # POST: data requested from all procedure outputs and sent to outputs
    @status()
    def validate(self) -> None:
        for input in self.__new_inputs:
            input.validate()
            if not input.is_status("validate", "OK"):
                self._set_status("validate", "INPUT_VALIDATION_FAIL")
                return
        for slot, input in self.__inputs.items():
            if input not in self.__new_inputs:
                continue
            assert(input.is_valid())
            data = input.get()
            self.__proc.put(slot, data)
            if self.__proc.is_status("put", "INVALID_VALUE"):
                self._set_status("validate", "INVALID_INPUT_VALUE")
                return
            if not self.__proc.is_status("put", "OK"):
                self._set_status("validate", "INVALID_PROCEDURE")
                return
            self.__new_inputs.remove(input)
        for slot, output in self.__outputs.items():
            data = self.__proc.get(slot)
            if not self.__proc.is_status("get", "OK"):
                self._set_status("validate", "INVALID_PROCEDURE")
                return
            output.put(data)
            if not output.is_status("put", "OK"):
                self._set_status("validate", "INVALID_PROCEDURE")
                return
        self._set_status("validate", "OK")


    # QUERIES

    # Get types of procedure outputs
    def get_output_types(self) -> dict[str, type]:
        return self.__output_types


class SimpleProcMeta(StatusMeta):
    def __new__(cls, class_name: str, bases: tuple[type, ...],
            namespace: dict[str, Any], **kwargs: Any) -> type:
        input_types = cls._get_field_types(class_name, namespace, "INPUTS")
        namespace["__input_types"] = input_types
        return super().__new__(cls, class_name, bases, namespace, **kwargs)

    @staticmethod
    def _get_field_types(class_name: str, namespace: dict[str, Any], key: str
            ) -> dict[str, type]:
        if "__annotations__" not in namespace or key not in namespace:
            return dict[str, type]()
        annotations = namespace["__annotations__"]
        types = dict[str, type]()
        for slot in namespace["INPUTS"]:
            if slot in annotations:
                types[slot] = annotations[slot]
                continue
            protected_field = f"_{slot}"
            if protected_field in annotations:
                types[slot] = annotations[protected_field]
                continue
            private_field = f"_{class_name}__{slot}"
            if private_field in annotations:
                types[slot] = annotations[private_field]
                continue
        return types


class SimpleProc(Procedure, metaclass=SimpleProcMeta):
    
    # CLASS QUERIES

    # Get names and types of input data slots
    @classmethod
    def get_input_types(cls) -> dict[str, type]:
        return getattr(cls, "__input_types")

    # Create procedure for given input types that are subtypes of the slot types
    @classmethod
    def create(cls, input_types: dict[str, type]) -> Procedure:
        return cls()

    
    # COMMANDS
    
    # Set input value
    # PRE: `slot` is input slot
    # PRE: `value` type is compatible
    # PRE: `value` is valid (fits procedure logic)
    # POST: input data in `slot` is set to `value`
    @status()
    def put(self, slot: str, value: Any) -> None:
        assert False


    # QUERIES

    # Get names and types of outputs
    def get_output_types(self) -> dict[str, type]:
        assert False

    # get value
    # PRE: `slot` is output slot
    # PRE: there is enough input data for calculation
    @status()
    def get(self, slot: str) -> Any:
        assert False


def _type_fits(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False
