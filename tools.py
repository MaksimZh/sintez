from typing import Any, Callable, final
from abc import ABC, ABCMeta

_METHOD_STATUS_NAME = "__method_status_name"
_METHOD_STATUSES = "__method_statuses"
_CLASS_STATUSES = "__class_statuses"

AnyFunc = Callable[..., Any]

# Decorator that adds status management to method
# and defines allowed status values.
# Note that if 'NIL' value is not listed it will be added automatically.
#
# Usage:
#    class Name(Status):
#        ...
#
#        # method with status 'method' that can have values 'VAL1' and 'VAL2'
#        @status("VAL1", "VAL2")
#        def method(self):
#            ...
#
#        # method with status 'alt_name' that can have values 'VAL3' and 'VAL4'
#        @status("VAL3", "VAL4", name="alt_name")
#        def method2(self):
#            ...
#
def status(*args: str, **kwargs: str) -> Callable[[AnyFunc], AnyFunc]:
    assert len(set(kwargs.keys()).difference(set(["name"]))) == 0, \
        f"Only 'name' keyword argument accepted"
    status_name = kwargs.get("name", "")
    def decorator(func: AnyFunc) -> AnyFunc:
        setattr(func, _METHOD_STATUSES, set(args))
        setattr(func, _METHOD_STATUS_NAME, status_name)
        return func
    return decorator


# Metaclass of Status base class.
# Note that it is child of ABCMeta and hence compatible with all ABC classes.
#
# Direct interaction with this metaclass not needed for regular status usage.
#
class StatusMeta(ABCMeta):
    def __new__(cls, class_name: str, bases: tuple[type, ...],
            namespace: dict[str, Any], **kwargs: Any) -> "StatusMeta":
        namespace[_CLASS_STATUSES] = dict()
        for name, item in namespace.items():
            if callable(item) and hasattr(item, _METHOD_STATUSES):
                status_name = getattr(item, _METHOD_STATUS_NAME)
                if status_name == "":
                    status_name = name
                status_values = getattr(item, _METHOD_STATUSES)
                if "NIL" not in status_values:
                    status_values.add("NIL")
                assert status_name not in namespace[_CLASS_STATUSES], \
                    f"Duplicate status '{status_name}' in {cls.__name__}"
                namespace[_CLASS_STATUSES][status_name] = status_values
        return super().__new__(cls, class_name, bases, namespace, **kwargs)


# Base class for all classes with status management.
# Note that this class is already child of ABC
# so you dont need to repeat ABC in base class list.
#
# This class asserts that all status names and values are correct,
# i.e. indicated with and within status decorators.
# Note that these asserts are disabled in release.
#
# Usage:
#     class Name(Status):
#        ...
#        # method with status
#        @status("VAL1", "VAL2")
#        def status_method(self):
#           ...
#
#        # method without status
#        def no_status_method(self):
#           ...
#
class Status(ABC, metaclass=StatusMeta):

    __status: dict[str, str]

    def __new__(cls: type["Status"]) -> "Status":
        if cls is Status:
            raise TypeError(f"Only children of {cls.__name__} may be instantiated")
        return super().__new__(cls)

    # CONSTRUCTOR
    # POST: all defined statuses are set to 'NIL'
    def __init__(self) -> None:
        self.__status = dict([(name, "NIL") \
            for name, _ in getattr(self, _CLASS_STATUSES).items()])

    
    # COMMANDS

    # Protected method that should be used by child classes to change statuses.
    # Checks preconditins with 'assert' statement (disabled in release).
    # PRE: 'name' is defined status name
    # PRE: 'value' is defined value for 'name' status
    # POST: status 'name' is changed to 'value'
    @final
    def _set_status(self, name: str, value: str) -> None:
        assert name in self.__status, self.__no_status_message(name)
        assert value in getattr(self, _CLASS_STATUSES)[name], \
            self.__no_status_value_message(name, value)
        self.__status[name] = value


    # QUERIES

    # Get status value by name.
    # Checks preconditins with 'assert' statement (disabled in release).
    # PRE: 'name' is defined status name
    @final
    def get_status(self, name: str) -> str:
        assert name in self.__status, self.__no_status_message(name)
        return self.__status[name]


    # Check if status 'name' has value 'value'.
    # Checks preconditins with 'assert' statement (disabled in release).
    # It is recommended to use this method for status check to make sure
    # the 'value' is defined value for 'name' status.
    # PRE: 'name' is defined status name
    # PRE: 'value' is defined value for 'name' status
    @final
    def is_status(self, name: str, value: str) -> bool:
        assert name in self.__status, self.__no_status_message(name)
        assert value in getattr(self, _CLASS_STATUSES)[name], \
            self.__no_status_value_message(name, value)
        return self.__status[name] == value


    def __no_status_message(self, name: str) -> str:
        return f"No '{name}' status for {self.__class__.__name__}"

    def __no_status_value_message(self, name: str, value: str) -> str:
        return f"No '{value}' value for '{name}' status of {self.__class__.__name__}"
