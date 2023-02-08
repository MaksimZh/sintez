from typing import Any, Callable, final, TypeVar
from abc import ABC, ABCMeta

_METHOD_STATUS_NAME = "__method_status_name"
_METHOD_STATUSES = "__method_statuses"
_CLASS_STATUSES = "__class_statuses"

T = TypeVar("T")
AnyFunc = Callable[..., T]

# Decorator that adds status management to method
# and defines allowed status values.
# Note that if 'NIL' value is not listed it will be added automatically.
#
# Usage:
#    # method with status 'method' that can have values 'VAL1' and 'VAL2'
#    @status("VAL1", "VAL2")
#    def method(self):
#        ...
#
#    # method with status 'alt_name' that can have values 'VAL3' and 'VAL4'
#    @status("VAL3", "VAL4", name="alt_name")
#    def method2(self):
#        ...
#
#    # method with same status and values that in parent class
#    @status()
#    def method3(self):
#        ...
#
#    # method with same status and values that in parent class
#    # parent class must have 'some_name' status
#    @status(name="some_name")
#    def method4(self):
#        ...
#
def status(*args: str, **kwargs: str) -> Callable[[AnyFunc[T]], AnyFunc[T]]:
    assert len(set(kwargs.keys()).difference(set(["name"]))) == 0, \
        f"Only 'name' keyword argument accepted"
    status_name = kwargs.get("name", "")
    status_values = set(args)
    if len(status_values) > 0 and "NIL" not in status_values:
        status_values.add("NIL")
    def decorator(func: AnyFunc[T]) -> AnyFunc[T]:
        setattr(func, _METHOD_STATUSES, status_values)
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
            namespace: dict[str, Any], **kwargs: Any) -> type:
        parent_statuses = set[str]()
        all_status_values = dict[str, set[str]]()
        for base in bases:
            if not hasattr(base, _CLASS_STATUSES):
                continue
            for name, values in getattr(base, _CLASS_STATUSES).items():
                parent_statuses.add(name)
                if name in all_status_values:
                    assert values == all_status_values[name]
                    continue
                all_status_values[name] = values
        for name, item in namespace.items():
            is_method_with_status = \
                callable(item) and hasattr(item, _METHOD_STATUSES)
            if not is_method_with_status:
                continue
            status_name = getattr(item, _METHOD_STATUS_NAME)
            if status_name == "":
                status_name = name
            assert status_name not in all_status_values \
                    or status_name in parent_statuses, \
                f"Duplicate status '{status_name}' in {cls.__name__}"
            status_values = getattr(item, _METHOD_STATUSES)
            if status_name in parent_statuses:
                assert len(status_values) == 0 \
                    or status_values == all_status_values[status_name], \
                    f"Values for '{status_name}' status changed in child class {class_name}"
                continue
            assert len(status_values) > 0, \
                f"No values provided for '{status_name}' status of {class_name}"
            all_status_values[status_name] = status_values
        namespace[_CLASS_STATUSES] = all_status_values
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
