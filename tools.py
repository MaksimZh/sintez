from typing import Any, Callable

_STATUSES = "__tools_statuses"

AnyFunc = Callable[..., Any]

def status(*args: str) -> Callable[[AnyFunc], AnyFunc]:
    def decorator(func: AnyFunc) -> AnyFunc:
        setattr(func, _STATUSES, set(args))
        return func
    return decorator


class Status:
    pass
