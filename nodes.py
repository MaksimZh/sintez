from typing import Any

class DataNode:
    
    def __init__(self, value_type: type) -> None:
        pass

    
class ProcNode:

    def __init__(self, proc_type: type) -> None:
        pass

    
    # COMMANDS

    def set_input(self, name: str, node: DataNode) -> None:
        pass

    def set_output(self, name: str, node: DataNode) -> None:
        pass


class Output:
    
    def put(self, name: str, value: Any) -> None:
        pass
