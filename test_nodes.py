import unittest

from nodes import ProcNode, DataNode, Input, Output

class AddProc:

    def __init__(self, input: Input, output: Output) -> None:
        self.__input = input
        self.__output = output
        self.__input.add("arg1", int)
        self.__input.add("arg2", int)
        self.__output.add("result", int)

    def run(self) -> None:
        arg1 = self.__input.get("arg1")
        arg2 = self.__input.get("arg2")
        self.__output.put("result", arg1 + arg2)


class Test(unittest.TestCase):

    def test(self):
        a = DataNode(int)
        b = DataNode(int)
        c = DataNode(int)
        p = ProcNode(AddProc)
        p.set_input("left", a)
        a.add_dest(p)
        p.set_input("right", b)
        b.add_dest(p)
        p.set_output("result", c)
        c.add_source(p)


if __name__ == "__main__":
    unittest.main()
