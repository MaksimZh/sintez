from typing import Any

class DataNode:
    
    def __init__(self, value_type: type) -> None:
        pass

    def add_source(self, source: "ProcNode") -> None:
        pass

    def add_dest(self, source: "ProcNode") -> None:
        pass

    
class ProcNode:

    def __init__(self, proc_type: type) -> None:
        pass

    
    # COMMANDS

    def set_input(self, name: str, node: DataNode) -> None:
        pass

    def set_output(self, name: str, node: DataNode) -> None:
        pass


class Input:

    def add(self, name: str, value_type: type) -> None:
        pass
    
    def get(self, name: str) -> Any:
        pass


class Output:

    def add(self, name: str, value_type: type) -> None:
        pass
    
    def put(self, name: str, value: Any) -> None:
        pass
