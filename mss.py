from typing import Any, Callable
import inspect

_METHOD_STATUS_SET_TNAME = "__status_set"
_CLASS_STATUS_SETS_NAME = "__status_sets"


def status(*args: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def _status(func: Callable[..., Any]) -> Callable[..., Any]:
        setattr(func, _METHOD_STATUS_SET_TNAME, set(args))
        return func
    return _status


class StatusMeta(type):
    def __new__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        attrs[_CLASS_STATUS_SETS_NAME] = dict()
        for name, value in attrs.items():
            if inspect.isfunction(value) and hasattr(value, _METHOD_STATUS_SET_TNAME):
                status_set = getattr(value, _METHOD_STATUS_SET_TNAME)
                if "NIL" not in status_set:
                    status_set.add("NIL")
                attrs[_CLASS_STATUS_SETS_NAME][name] = status_set
        return super().__new__(cls, name, bases, attrs)


class Status(metaclass=StatusMeta):
        
    __status: dict[str, str]

    def __init__(self) -> None:
        self.__status = dict()
        for key in getattr(self, _CLASS_STATUS_SETS_NAME):
            self.__status[key] = "NIL"

    def _set_status(self, name: str, value: str) -> None:
        assert name in getattr(self, _CLASS_STATUS_SETS_NAME), \
            "No " + self.__class__.__qualname__ + "." + name + " status"
        assert value in getattr(self, _CLASS_STATUS_SETS_NAME)[name], \
            "Status " + self.__class__.__qualname__ + "." + name + " has no '" + value + "' variant"
        self.__status[name] = value

    def get_status(self, name: str) -> str:
        assert name in getattr(self, _CLASS_STATUS_SETS_NAME), \
            "No " + self.__class__.__qualname__ + "." + name + " status"
        return self.__status[name]

    def is_status_equal(self, name: str, value: str) -> bool:
        assert name in getattr(self, _CLASS_STATUS_SETS_NAME), \
            "No " + self.__class__.__qualname__ + "." + name + " status"
        assert value in getattr(self, _CLASS_STATUS_SETS_NAME)[name], \
            "Status " + self.__class__.__qualname__ + "." + name + " has no '" + value + "' variant"
        return self.__status[name] == value

    def is_status_not_equal(self, name: str, value: str) -> bool:
        assert name in getattr(self, _CLASS_STATUS_SETS_NAME), \
            "No " + self.__class__.__qualname__ + "." + name + " status"
        assert value in getattr(self, _CLASS_STATUS_SETS_NAME)[name], \
            "Status " + self.__class__.__qualname__ + "." + name + " has no '" + value + "' variant"
        return self.__status[name] != value
