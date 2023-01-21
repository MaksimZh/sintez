from typing import Any, Callable, final
from abc import ABC

_STATUSES = "__tools_statuses"

AnyFunc = Callable[..., Any]

def status(*args: str) -> Callable[[AnyFunc], AnyFunc]:
    def decorator(func: AnyFunc) -> AnyFunc:
        setattr(func, _STATUSES, set(args))
        return func
    return decorator


class Status(ABC):

    __status: dict[str, str]

    def __new__(cls: type["Status"]) -> "Status":
        if cls is Status:
            raise TypeError(f"only children of '{cls.__name__}' may be instantiated")
        return super().__new__(cls)

    def __init__(self) -> None:
        self.__status = dict()
    
    @final
    def get_status(self, name: str) -> str:
        return self.__status.get(name, "NIL")

    @final
    def _set_status(self, name: str, value: str) -> None:
        self.__status[name] = value
