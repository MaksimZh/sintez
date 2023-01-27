from typing import Any, Optional, Union, final, Type
from abc import abstractmethod
from tools import Status, status

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
    # POST: `output` is added to outputs
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
    # POST: send data to all outputs with `put` command
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
    # PRE: input procedure node accepts connection
    #      of data with `data_type` type to output `slot`
    # POST: input procedure node is set to `input`
    # POST: if `input` is not None add this node to `input` output slot `slot`
    # POST: no output procedure nodes
    # POST: data type is set to `data_type`
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
    # POST: `output` is added to outputs
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
    # POST: data is set to `value`
    # POST: if data was valid send `invalidate` command to all outputs
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
    # POST: if data is valid then send `invalidate` command to all outputs
    # POST: data is invalid
    def invalidate(self) -> None:
        if not self.is_valid():
            return
        self.__is_valid = False
        for output in self.__outputs:
            output.invalidate(self)

    # Make sure data is valid
    # PRE: data is valid or input procedure can be validated
    # POST: if data is invalid then send `validate` command to input
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
# Contains:
#     - named and typed input values
#     - named and typed output values 
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
    def create(cls, inputs: dict[str, type]) -> "Procedure":
        assert False

    
    # COMMANDS
    
    # Set input value
    # PRE: `name` is input slot
    # PRE: `value` type is compatible
    # PRE: `value` is valid (fits procedure logic)
    # POST: input value is set
    @abstractmethod
    @status("OK", "INVALID_NAME", "INCOMPATIBLE_TYPE", "INVALID_VALUE")
    def put(self, name: str, value: Any) -> None:
        assert False


    # QUERIES

    # Get names and types of outputs
    @abstractmethod
    def get_output_types(self) -> dict[str, type]:
        assert False

    # get value
    # PRE: `name` is output slot
    # PRE: there is enough data to calculate value
    @abstractmethod
    @status("OK", "INVALID_NAME", "INCOMPLETE_INPUT")
    def get(self, name: str) -> Any:
        assert False


# Implements procedure node part of calculation scheme logic.
#
# Contains:
#     - input data nodes (any number)
#     - output data nodes (any number)
#     - procedure
#     - input data statuses (new or used)
#
@final
class ProcNode(InputProc, OutputProc):

    __proc: Procedure
    __output_types: dict[str, type]
    __inputs: dict[str, InputData]
    __outputs: dict[str, OutputData]
    __new_inputs: set[InputData]


    # CONSTRUCTOR
    # PRE: `inputs` fit `proc_type.get_input_types`
    # POST: `inputs` are connected to input slots
    # POST: no output nodes
    # POST: create procedure using `proc_type.create`
    # POST: all inputs are new
    # POST: send `add_output` command to all inputs
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
    # POST: mark `input` as new
    # POST: send `invalidate` command to all outputs
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
    # PRE: procedure accepts input data of types given by `get_input_types`
    # PRE: procedure provides output data of types given by `get_output_types`
    # POST: send `validate`` command to all inputs
    # POST: obtain data from new inputs with `get` query
    # POST: send data from new inputs to procedure with `put` command
    # POST: send data to all outputs with `put` command
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


# TODO:
# DEPRECATED:

# Nodes implement the calculation scheme logic.
#
# ValueNode can be linked only to ProcedureNodes and vice versa.
# All links have one and only one direction, no loops allowed.
# The basic concepts of calculation are invalidation and validation.
# Value change invalidates all succeeding nodes.
# Procedure validation also validates all its output nodes.
# When node is invalidated it invalidates all succeeding nodes.
# When node is validated it requests validation of all preceding nodes.
#
# When node is created its build is incomplete.
# Inputs and outputs can be added only before build is complete.
# Manipulations concerning calculation logic are forbidden until build is complete.


# Implements value node part of calculation scheme logic.
# Can have only one (optional) input procedure.
# So there is only one component responsible for value update.
#
# Note that value must be validated before `get` query is used.
#
# Contains:
#     - input procedure node (optional)
#     - output procedure nodes (any number)
#     - value type
#     - build status
#     - value status (valid or not)
#     - value (optional)
#
@final
class ValueNode(Status):

    __input: Optional["ProcedureNode"]
    __outputs: set["ProcedureNode"]
    __value_type: type
    __build_complete: bool
    __is_valid: bool
    __value: Any

    # CONSTRUCTOR
    # POST: no input node
    # POST: no output nodes
    # POST: value type is set
    # POST: build not complete
    def __init__(self, value_type: type) -> None:
        super().__init__()
        self.__value_type = value_type
        self.__is_valid = False
        self.__input = None
        self.__outputs = set()
        self.__build_complete = False


    # COMMANDS

    # add input node
    # PRE: build not complete
    # PRE: `input` is not in input or outputs
    # PRE: this node has no inputs
    # POST: input is set to `input`
    @status("OK", "BUILD_COMPLETE", "ALREADY_LINKED", "TOO_MANY_INPUTS")
    def add_input(self, input: "ProcedureNode") -> None:
        if self.__build_complete:
            self._set_status("add_input", "BUILD_COMPLETE")
            return
        if input in self.__outputs or input is self.__input:
            self._set_status("add_input", "ALREADY_LINKED")
            return
        if self.__input is not None:
            self._set_status("add_input", "TOO_MANY_INPUTS")
            return
        self.__input = input
        self._set_status("add_input", "OK")

    # add output node
    # PRE: build not complete
    # PRE: `output` is not in input or outputs
    # POST: `output` added to output nodes
    @status("OK", "BUILD_COMPLETE", "ALREADY_LINKED")
    def add_output(self, output: "ProcedureNode") -> None:
        if self.__build_complete:
            self._set_status("add_output", "BUILD_COMPLETE")
            return
        if output in self.__outputs or output is self.__input:
            self._set_status("add_output", "ALREADY_LINKED")
            return
        self.__outputs.add(output)
        self._set_status("add_output", "OK")

    # complete build
    # POST: build complete
    # POST: value is invalid
    def complete_build(self) -> None:
        self.__build_complete = True


    # put value
    # PRE: build complete
    # PRE: `value` can be implicitly converted to node type
    # POST: make value new for all outputs
    # POST: value is set to `value`
    # POST: send invalidate command to all outputs
    # POST: no outputs used NEW value
    @status("OK", "BUILD_INCOMPLETE", "INCOMPATIBLE_TYPE")
    def put(self, value: Any) -> None:
        if not self.__build_complete:
            self._set_status("put", "BUILD_INCOMPLETE")
            return
        if not _type_fits(type(value), self.__value_type):
            self._set_status("put", "INCOMPATIBLE_TYPE")
            return
        self._set_status("put", "OK")
        self.__value = value
        self.__is_valid = True
        for output in self.__outputs:
            output.invalidate(self)
            assert output.is_status("invalidate", "OK")


    # invalidate node
    # PRE: build complete
    # POST: value is invalid
    # POST: if value was valid then make it new for all outputs
    @status("OK", "BUILD_INCOMPLETE")
    def invalidate(self) -> None:
        if not self.__build_complete:
            self._set_status("invalidate", "BUILD_INCOMPLETE")
            return
        self._set_status("invalidate", "OK")
        if not self.is_valid():
            return
        self.__is_valid = False
        for output in self.__outputs:
            output.invalidate(self)
            assert output.is_status("invalidate", "OK")


    # ensure that the value is valid
    # PRE: build complete
    # PRE: there is input or the value is valid
    # POST: if the value is invalid then send validate command to input
    @status("OK", "BUILD_INCOMPLETE", "NO_VALUE_SOURCE", "INPUT_FAILED")
    def validate(self) -> None:
        if not self.__build_complete:
            self._set_status("validate", "BUILD_INCOMPLETE")
            return
        if self.is_valid():
            self._set_status("validate", "OK")
            return
        if self.__input is None:
            self._set_status("validate", "NO_VALUE_SOURCE")
            return
        assert self.__input
        self.__input.validate()
        if not self.__input.is_status("validate", "OK"):
            self._set_status("validate", "INPUT_FAILED")
            return
        self._set_status("validate", "OK")


    # QUERIES

    # get data type
    def get_type(self) -> type:
        return self.__value_type

    # get input node
    def get_input(self) -> Optional["ProcedureNode"]:
        return self.__input

    # get set of output nodes
    def get_outputs(self) -> set["ProcedureNode"]:
        return self.__outputs.copy()

    # check is value is valid
    @status("OK", "BUILD_INCOMPLETE")
    def is_valid(self) -> bool:
        if not self.__build_complete:
            self._set_status("is_valid", "BUILD_INCOMPLETE")
            return False
        self._set_status("is_valid", "OK")
        return self.__is_valid


    # get value
    # PRE: build complete
    # PRE: value is value
    @status("OK", "BUILD_INCOMPLETE", "INVALID_VALUE")
    def get(self) -> Any:
        if not self.__build_complete:
            self._set_status("get", "BUILD_INCOMPLETE")
            return None
        if not self.is_valid():
            self._set_status("get", "INVALID_VALUE")
            return None
        self._set_status("get", "OK")
        return self.__value


# Implements procedure node part of calculation scheme logic.
#
# Contains:
#     - input value nodes (any number)
#     - output procedure nodes (any number)
#     - build status
#     - procedure
#     - input value statuses (new or used)
#
@final
class ProcedureNode(Status):

    __procedure: Procedure
    __inputs: dict[str, ValueNode]
    __outputs: dict[str, ValueNode]
    __build_complete: bool
    __new_inputs: set[ValueNode]

    # CONSTRUCTOR
    # POST: no input nodes
    # POST: no output nodes
    # POST: procedure is set
    # POST: build not complete
    def __init__(self, procedure: Procedure) -> None:
        super().__init__()
        self.__procedure = procedure
        self.__inputs = dict()
        self.__outputs = dict()
        self.__build_complete = False
        self.__new_inputs = set()


    # COMMANDS

    # add input node
    # PRE: build not complete
    # PRE: `input` is not in inputs or outputs
    # PRE: `name` is not occupied
    # POST: `input` added to inputs with `name`
    @status("OK", "BUILD_COMPLETE", "ALREADY_LINKED", "DUPLICATE_NAME")
    def add_input(self, name: str, input: ValueNode) -> None:
        if self.__build_complete:
            self._set_status("add_input", "BUILD_COMPLETE")
            return
        if self.__is_node_linked(input):
            self._set_status("add_input", "ALREADY_LINKED")
            return
        if self.__is_slot_linked(name):
            self._set_status("add_input", "DUPLICATE_NAME")
            return
        self.__inputs[name] = input
        self._set_status("add_input", "OK")


    # add output node
    # PRE: build not complete
    # PRE: `output` is not in inputs or outputs
    # PRE: `name` is not occupied
    # POST: `output` added to outputs with `name`
    @status("OK", "ALREADY_LINKED", "DUPLICATE_NAME", "BUILD_COMPLETE")
    def add_output(self, name: str, output: ValueNode) -> None:
        if self.__build_complete:
            self._set_status("add_output", "BUILD_COMPLETE")
            return
        if self.__is_node_linked(output):
            self._set_status("add_output", "ALREADY_LINKED")
            return
        if self.__is_slot_linked(name):
            self._set_status("add_output", "DUPLICATE_NAME")
            return
        self.__outputs[name] = output
        self._set_status("add_output", "OK")


    # complete build
    # POST: build complete
    def complete_build(self) -> None:
        self.__build_complete = True


    # signal that input has changed
    # PRE: build complete
    # PRE: `input` is in node inputs
    # POST: all outputs get invalidate command
    @status("OK", "BUILD_INCOMPLETE", "NOT_INPUT")
    def invalidate(self, input: ValueNode) -> None:
        if not self.__build_complete:
            self._set_status("invalidate", "BUILD_INCOMPLETE")
            return
        if input not in self.__inputs.values():
            self._set_status("invalidate", "NOT_INPUT")
            return
        self.__new_inputs.add(input)
        self._set_status("invalidate", "OK")
        for output in self.__outputs.values():
            output.invalidate()
            assert output.is_status("invalidate", "OK")


    # make procedure outputs up to date with inputs
    # PRE: build complete
    # PRE: inputs are valid or can be validated
    # PRE: inputs and outputs names and types compatible with the procedure
    # POST: all inputs have been validated
    # POST: values from all new inputs requested with `get` query
    # POST: values of all new inputs sent to procedure with `put` command
    # POST: all inputs are considered used
    # POST: all outputs have been updated using procedure `get` query
    @status("OK", "BUILD_INCOMPLETE", "INPUT_VALIDATION_FAILED", "FAIL")
    def validate(self) -> None:
        if not self.__build_complete:
            self._set_status("validate", "BUILD_INCOMPLETE")
            return
        for input in self.__inputs.values():
            input.validate()
            if not input.is_status("validate", "OK"):
                self._set_status("validate", "INPUT_VALIDATION_FAILED")
                return
        for name, input in self.__inputs.items():
            if input not in self.__new_inputs:
                continue
            is_valid = input.is_valid()
            assert input.is_status("is_valid", "OK")
            assert is_valid
            value = input.get()
            assert input.is_status("get", "OK")
            self.__procedure.put(name, value)
            if not self.__procedure.is_status("put", "OK"):
                self._set_status("validate", "FAIL")
                return
            self.__new_inputs.remove(input)
        for name, output in self.__outputs.items():
            value = self.__procedure.get(name)
            if not self.__procedure.is_status("get", "OK"):
                self._set_status("validate", "FAIL")
                return
            output.put(value)
            if not output.is_status("put", "OK"):
                self._set_status("validate", "FAIL")
                return
        self._set_status("validate", "OK")


    # QUERIES

    # get dictionary of input nodes
    def get_inputs(self) -> dict[str, "ValueNode"]:
        return self.__inputs.copy()

    # get dictionary of output nodes
    def get_outputs(self) -> dict[str, "ValueNode"]:
        return self.__outputs.copy()


    def __is_node_linked(self, node: ValueNode) -> bool:
        return node in self.__inputs.values() \
            or node in self.__outputs.values()

    def __is_slot_linked(self, name: str) -> bool:
        return name in self.__inputs \
            or name in self.__outputs


ValueLink = Union[str, type]
ValuePattern = tuple[str, type]
ProcPattern = tuple[Procedure, dict[str, ValueLink], dict[str, ValueLink]]
NodePattern = Union[ValuePattern, ProcPattern]

# Special kind of procedure that contains calculation scheme built using
# its declarative description sent to constructor.
#
# The description is list of value and procedure patterns.
# Value pattern is the following tuple:
#     ("name", ValueType).
# Procedure pattern is the following tuple:
#     (ProcedureType, <input_dictionary>, <output_dictionary>).
# Entries in input and output dictionaries are of the following two kinds:
#     "name_in_procedure": "value_node_name" - link to value node by name
#     "name_in_procedure_and_outside": Type - create value node and link to it
# If multiple I/O entries of the 2nd kind have the same name
# then their types must match. 
#
class Simulator(Procedure):

    __values: dict[str, ValueNode]
    __procs: list[ProcedureNode]
    __auto_value_types: dict[str, type]

    # CONSTRUCTOR
    # PRE: patterns have no duplicate names
    # PRE: all procedure IO names present in value patterns
    # PRE: no duplicate links
    # PRE: no multiple value inputs
    # POST: nodes linked and build complete for all nodes
    @status(
        "OK",
        "DUPLICATE_NAME",
        "NAME_NOT_FOUND",
        "ALREADY_LINKED",
        "TOO_MANY_INPUTS",
        "AUTO_VALUE_TYPE_MISMATCH",
        name="init",
    )
    def __init__(self, node_patterns: list[NodePattern]) -> None:
        super().__init__()
        self.__init_status = "NIL"
        self.__init_message = ""
        value_patterns = []
        proc_patterns = []
        for pattern in node_patterns:
            match pattern:
                case (_, _):
                    value_patterns.append(pattern)
                case (_, _, _):
                    proc_patterns.append(pattern)

        self.__init_values(value_patterns)
        if not self.is_status("init", "NIL"):
            return
        self.__init_procs(proc_patterns)
        if not self.is_status("init", "NIL"):
            return
        for value in self.__values.values():
            value.complete_build()
        for proc in self.__procs:
            proc.complete_build()
        self._set_status("init", "OK")
    __init_message: str

    @final
    def get_init_message(self) -> str:
        return self.__init_message


    def __init_values(self, patterns: list[ValuePattern]) -> None:
        self.__values = dict()
        for name, value_type in patterns:
            if name in self.__values:
                self._set_status("init", "DUPLICATE_NAME")
                self.__init_message = f"Duplicate name: '{name}'"
                return
            self.__values[name] = ValueNode(value_type)


    def __init_procs(self, patterns: list[ProcPattern]) -> None:
        self.__procs = list()
        self.__auto_value_types = dict()
        for proc_type, inputs, outputs in patterns:
            proc = ProcedureNode(proc_type)
            self.__add_inputs(proc, inputs)
            if self.__init_status != "NIL":
                return
            self.__add_outputs(proc, outputs)
            if self.__init_status != "NIL":
                return
            self.__procs.append(proc)


    def __add_inputs(self, proc: ProcedureNode, inputs: dict[str, ValueLink]) -> None:
        for slot_name, value_link in inputs.items():
            if type(value_link) is type:
                value_name = slot_name
                self.__add_auto_value(value_name, value_link)
                if self.__init_status != "NIL":
                    return
            else:
                assert type(value_link) is str
                value_name: str = value_link
            if value_name not in self.__values:
                self._set_status("init", "NAME_NOT_FOUND")
                self.__init_message = f"Input not found: '{slot_name}': '{value_name}'"
                return
            value = self.__values[value_name]
            self.__add_input(proc, slot_name, value)
            if self.is_status("init", "ALREADY_LINKED"):
                self.__init_message = f"Already linked: '{slot_name}': '{value_name}'"
                return

    def __add_outputs(self, proc: ProcedureNode, outputs: dict[str, ValueLink]) -> None:
        for slot_name, value_link in outputs.items():
            if type(value_link) is type:
                value_name = slot_name
                self.__add_auto_value(value_name, value_link)
                if self.__init_status != "NIL":
                    return
            else:
                assert type(value_link) is str
                value_name: str = value_link
            if value_name not in self.__values:
                self._set_status("init", "NAME_NOT_FOUND")
                self.__init_message = f"Output not found: '{slot_name}': '{value_name}'"
                return
            value = self.__values[value_name]
            self.__add_output(proc, slot_name, value)
            if self.is_status("init", "ALREADY_LINKED"):
                self.__init_message = f"Already linked: '{slot_name}': '{value_name}'"
                return
            if self.is_status("init", "TOO_MANY_INPUTS"):
                self.__init_message = f"Too many inputs: '{slot_name}': '{value_name}'"
                return

    def __add_auto_value(self, name: str, value_type: type) -> None:
        if name not in self.__values:
            assert name not in self.__auto_value_types
            self.__auto_value_types[name] = value_type
            self.__values[name] = ValueNode(value_type)
            return
        assert name in self.__auto_value_types
        if self.__auto_value_types[name] is not value_type:
            self._set_status("init", "AUTO_VALUE_TYPE_MISMATCH")
            self.__init_message = \
                f"Auto value '{name}' type mismatch:" + \
                    f" {str(value_type)} and {str(self.__auto_value_types[name])}"

    def __add_input(self, proc: ProcedureNode, slot_name: str, value: ValueNode) -> None:
        value.add_output(proc)
        if value.get_status("add_output") == "ALREADY_LINKED":
            self._set_status("init", "ALREADY_LINKED")
            return
        assert value.get_status("add_output") == "OK"
        proc.add_input(slot_name, value)
        if proc.get_status("add_input") == "ALREADY_LINKED":
            self._set_status("init", "ALREADY_LINKED")
            return
        assert proc.get_status("add_input") == "OK"

    def __add_output(self, proc: ProcedureNode, slot_name: str, value: ValueNode) -> None:
        proc.add_output(slot_name, value)
        if proc.is_status("add_output", "ALREADY_LINKED"):
            self._set_status("init", "ALREADY_LINKED")
            return
        assert proc.is_status("add_output", "OK")
        value.add_input(proc)
        if value.get_status("add_input") == "ALREADY_LINKED":
            self._set_status("init", "ALREADY_LINKED")
            return
        if value.get_status("add_input") == "TOO_MANY_INPUTS":
            self._set_status("init", "TOO_MANY_INPUTS")
            return
        assert value.get_status("add_input") == "OK"


    # COMMANDS

    @final
    @status()
    def put(self, name: str, value: Any) -> None:
        if not self.is_status("init", "OK"):
            self._set_status("put", "INTERNAL_ERROR")
            return
        if name not in self.__values:
            self._set_status("put", "INVALID_NAME")
            return
        if self.__values[name].get_input() is not None:
            self._set_status("put", "INVALID_NAME")
            return
        self.__values[name].put(value)
        assert self.__values[name].is_status("put", "OK")
        self._set_status("put", "OK")


    # QUERIES

    @final
    @status()
    def get(self, name: str) -> Any:
        if not self.is_status("init", "OK"):
            self._set_status("get", "INTERNAL_ERROR")
            return
        if name not in self.__values:
            self._set_status("get", "INVALID_NAME")
            return
        node = self.__values[name]
        node.validate()
        if not node.is_status("validate", "OK"):
            self._set_status("get", "INCOMPLETE_INPUT")
            return None
        value = node.get()
        assert node.is_status("get", "OK")
        self._set_status("get", "OK")
        return value


def _type_fits(t: type, required: type) -> bool:
    if issubclass(t, required):
        return True
    if required is complex:
        return t is int or t is float
    if required is float:
        return t is int
    return False
