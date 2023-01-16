import unittest

from nodes import ProcNode, DataNode, Output

class AddProc:

    __arg1: int
    __arg2: int
    __output: Output

    def __init__(self, output: Output) -> None:
        self.__output = output

    def set_input(self, name: str, value: int) -> None:
        if name == "arg1":
            self.__arg1 = value
            return
        if name == "arg2":
            self.__arg1 = value
            return
        assert(False)

    def run(self) -> None:
        self.__output.put("result", self.__arg1 + self.__arg2)

    def has_input(self, name: str) -> bool:
        return name in ["arg1", "arg2"]

    def has_output(self, name: str) -> bool:
        return name in ["result"]


class Test(unittest.TestCase):

    def test(self):
        a = DataNode(int)
        b = DataNode(int)
        c = DataNode(int)
        p = ProcNode(AddProc)
        p.set_input("left", a)
        p.set_input("right", b)
        p.set_output("result", c)


if __name__ == "__main__":
    unittest.main()
