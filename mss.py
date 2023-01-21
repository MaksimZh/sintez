from typing import Any, Callable
import inspect
from abc import ABC, ABCMeta

_METHOD_STATUS_VARS = "__mss_method_status_vars"
_CLASS_STATUS_VARS = "__mss_class_status_vars"


def status(*args: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def _status(func: Callable[..., Any]) -> Callable[..., Any]:
        setattr(func, _METHOD_STATUS_VARS, set(args))
        return func
    return _status


class StatusMeta(type):
    def __new__(cls, class_name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        attrs[_CLASS_STATUS_VARS] = dict()
        for name, value in attrs.items():
            if inspect.isfunction(value) and hasattr(value, _METHOD_STATUS_VARS):
                status_set = getattr(value, _METHOD_STATUS_VARS)
                if "NIL" not in status_set:
                    status_set.add("NIL")
                attrs[_CLASS_STATUS_VARS][name] = status_set
        return super().__new__(cls, class_name, bases, attrs)


class ABCStatusMeta(ABCMeta, StatusMeta):
    pass


class Status(metaclass=StatusMeta):
        
    __status: dict[str, str]

    def __init__(self) -> None:
        self.__status = dict()
        for key in getattr(self, _CLASS_STATUS_VARS):
            self.__status[key] = "NIL"

    def _set_status(self, name: str, value: str) -> None:
        assert name in getattr(self, _CLASS_STATUS_VARS), \
            "No " + self.__class__.__qualname__ + "." + name + " status"
        assert value in getattr(self, _CLASS_STATUS_VARS)[name], \
            "Status " + self.__class__.__qualname__ + "." + name + " has no '" + value + "' variant"
        self.__status[name] = value

    def get_status(self, name: str) -> str:
        assert name in getattr(self, _CLASS_STATUS_VARS), \
            "No " + self.__class__.__qualname__ + "." + name + " status"
        return self.__status[name]

    def is_status(self, name: str, value: str) -> bool:
        assert name in getattr(self, _CLASS_STATUS_VARS), \
            "No " + self.__class__.__qualname__ + "." + name + " status"
        assert value in getattr(self, _CLASS_STATUS_VARS)[name], \
            "Status " + self.__class__.__qualname__ + "." + name + " has no '" + value + "' variant"
        return self.__status[name] == value


class ABCStatus(ABC, Status, metaclass=ABCStatusMeta):
    pass
