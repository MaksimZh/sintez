from typing import Any, Callable

_STATUSES = "__tools_statuses"

AnyFunc = Callable[..., Any]

def status(*args: str) -> Callable[[AnyFunc], AnyFunc]:
    def decorator(func: AnyFunc) -> AnyFunc:
        setattr(func, _STATUSES, set(args))
        return func
    return decorator


class Status():

    __status: dict[str, str]

    def __init__(self) -> None:
        self.__status = dict()
    
    def get_status(self, name: str) -> str:
        return self.__status.get(name, "NIL")

    def _set_status(self, name: str, value: str) -> None:
        self.__status[name] = value
