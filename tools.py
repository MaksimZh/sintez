from typing import Any, Callable, final
from abc import ABC, ABCMeta

_METHOD_STATUSES = "__method_statuses"
_CLASS_STATUSES = "__class_statuses"

AnyFunc = Callable[..., Any]

def status(*args: str) -> Callable[[AnyFunc], AnyFunc]:
    def decorator(func: AnyFunc) -> AnyFunc:
        setattr(func, _METHOD_STATUSES, set(args))
        return func
    return decorator


class StatusMeta(ABCMeta):
    def __new__(cls, class_name: str, bases: tuple[type, ...],
            namespace: dict[str, Any], **kwargs: Any) -> "StatusMeta":
        namespace[_CLASS_STATUSES] = dict()
        for name, item in namespace.items():
            if callable(item) and hasattr(item, _METHOD_STATUSES):
                namespace[_CLASS_STATUSES][name] = getattr(item, _METHOD_STATUSES)
        return super().__new__(cls, class_name, bases, namespace, **kwargs)


class Status(ABC, metaclass=StatusMeta):

    __status: dict[str, str]

    def __new__(cls: type["Status"]) -> "Status":
        if cls is Status:
            raise TypeError(f"Only children of {cls.__name__} may be instantiated")
        return super().__new__(cls)

    def __init__(self) -> None:
        self.__status = dict([(name, "NIL") \
            for name, _ in getattr(self, _CLASS_STATUSES).items()])
    
    @final
    def get_status(self, name: str) -> str:
        assert name in self.__status, self.__no_status_message(name)
        return self.__status[name]

    @final
    def _set_status(self, name: str, value: str) -> None:
        assert name in self.__status, self.__no_status_message(name)
        assert value in getattr(self, _CLASS_STATUSES)[name], \
            self.__no_status_value_message(name, value)
        self.__status[name] = value

    def __no_status_message(self, name: str) -> str:
        return f"No '{name}' status for {self.__class__.__name__}"

    def __no_status_value_message(self, name: str, value: str) -> str:
        return f"No '{value}' value for '{name}' status of {self.__class__.__name__}"
