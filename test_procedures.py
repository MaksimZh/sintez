import unittest

from typing import Any

from tools import status
from procedures import Calculator, Composition
from procedures import Node, SlotNode, ProcNode, NodeVisitor


class Divmod(Calculator):

    INPUTS = ["left", "right"]
    OUTPUTS = ["quotient", "remainder"]
    __left: int
    __right: int
    __quotient: int
    __remainder: int

    # Check input value
    def _is_valid_value(self, slot: str, value: Any) -> bool:
        if slot == "right":
            return value != 0
        return True

    @status()
    def calculate(self) -> None:
        if self.__right < 0:
            self._set_status("calculate", "ERROR")
            return
        self.__quotient, self.__remainder = divmod(self.__left, self.__right)
        self._set_status("calculate", "OK")


class Test_Calculator(unittest.TestCase):

    def test_slots(self):
        dm = Divmod()
        self.assertEqual(dm.get_input_slots(), {"left": int, "right": int})
        self.assertEqual(dm.get_output_slots(), {"quotient": int, "remainder": int})


    def test_set(self):
        dm = Divmod()
        dm.put("left", 101)
        self.assertTrue(dm.is_status("put", "OK"))
        dm.put("middle", 1)
        self.assertTrue(dm.is_status("put", "INVALID_SLOT"))
        dm.put("quotient", 1)
        self.assertTrue(dm.is_status("put", "INVALID_SLOT"))
        dm.put("right", "foo")
        self.assertTrue(dm.is_status("put", "INVALID_TYPE"))
        dm.put("right", 0)
        self.assertTrue(dm.is_status("put", "INVALID_VALUE"))
        dm.put("right", 7)
        self.assertTrue(dm.is_status("put", "OK"))
        dm.put("left", 42)
        self.assertTrue(dm.is_status("put", "OK"))
        dm.put("right", 17)
        self.assertTrue(dm.is_status("put", "OK"))


    def test_run_success(self):
        dm = Divmod()
        self.assertTrue(dm.needs_run())
        dm.put("left", 101)
        dm.put("right", 7)
        self.assertTrue(dm.needs_run())
        dm.run()
        self.assertTrue(dm.is_status("run", "OK"))
        self.assertFalse(dm.needs_run())
        dm.put("left", 11)
        self.assertTrue(dm.needs_run())
        dm.run()
        self.assertTrue(dm.is_status("run", "OK"))
        self.assertFalse(dm.needs_run())


    def test_run_missing_input(self):
        dm = Divmod()
        dm.put("left", 101)
        dm.run()
        self.assertTrue(dm.is_status("run", "INVALID_INPUT"))
        self.assertTrue(dm.needs_run())


    def test_run_fail(self):
        dm = Divmod()
        dm.put("left", 101)
        dm.put("right", -7)
        dm.run()
        self.assertTrue(dm.is_status("run", "RUN_FAILED"))
        self.assertTrue(dm.needs_run())


    def test_get(self):
        dm = Divmod()
        dm.put("left", 101)
        dm.put("right", 7)
        dm.get("foo")
        self.assertTrue(dm.is_status("get", "INVALID_SLOT"))
        dm.get("quotient")
        self.assertTrue(dm.is_status("get", "NEEDS_RUN"))
        dm.run()
        self.assertEqual(dm.get("quotient"), 14)
        self.assertTrue(dm.is_status("get", "OK"))
        self.assertEqual(dm.get("remainder"), 3)
        self.assertTrue(dm.is_status("get", "OK"))


class Test_Composition(unittest.TestCase):

    def test_slots(self):
        # d, e = divmod(a, b)
        # f, g = divmod(e, c)
        comp = Composition([
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "d", "remainder": "e"}),
            (Divmod(),
                {"left": "e", "right": "c"},
                {"quotient": "f", "remainder": "g"}),
            ])
        self.assertTrue(comp.is_status("init", "OK"))
        self.assertEqual(comp.get_input_slots(), {"a": int, "b": int, "c": int})
        self.assertEqual(comp.get_output_slots(), {"d": int, "f": int, "g": int})


    def test_set(self):
        # d, e = divmod(a, b)
        # f, g = divmod(e, c)
        comp = Composition([
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "d", "remainder": "e"}),
            (Divmod(),
                {"left": "e", "right": "c"},
                {"quotient": "f", "remainder": "g"}),
            ])
        comp.put("a", 101)
        self.assertTrue(comp.is_status("put", "OK"))
        comp.put("foo", 101)
        self.assertTrue(comp.is_status("put", "INVALID_SLOT"))
        comp.put("e", 101)
        self.assertTrue(comp.is_status("put", "INVALID_SLOT"))
        comp.put("quotient", 101)
        self.assertTrue(comp.is_status("put", "INVALID_SLOT"))
        comp.put("f", 101)
        self.assertTrue(comp.is_status("put", "INVALID_SLOT"))
        comp.put("a", "foo")
        self.assertTrue(comp.is_status("put", "INVALID_TYPE"))
        comp.put("b", 0)
        self.assertTrue(comp.is_status("put", "INVALID_VALUE"))
        comp.put("b", 7)
        self.assertTrue(comp.is_status("put", "OK"))
        comp.put("c", 3)
        self.assertTrue(comp.is_status("put", "OK"))
        comp.put("a", 101)
        self.assertTrue(comp.is_status("put", "OK"))
        comp.put("b", 17)
        self.assertTrue(comp.is_status("put", "OK"))
        comp.put("c", 13)
        self.assertTrue(comp.is_status("put", "OK"))


    def test_run_success(self):
        # d, e = divmod(a, b)
        # f, g = divmod(e, c)
        comp = Composition([
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "d", "remainder": "e"}),
            (Divmod(),
                {"left": "e", "right": "c"},
                {"quotient": "f", "remainder": "g"}),
            ])
        self.assertTrue(comp.needs_run())
        comp.put("a", 117)
        comp.put("b", 20)
        comp.put("c", 5)
        self.assertTrue(comp.needs_run())
        comp.run()
        self.assertTrue(comp.is_status("run", "OK"))
        self.assertFalse(comp.needs_run())
        comp.put("b", 40)
        self.assertTrue(comp.needs_run())
        comp.run()
        self.assertTrue(comp.is_status("run", "OK"))
        self.assertFalse(comp.needs_run())


    def test_get(self):
        # d, e = divmod(a, b)
        # f, g = divmod(e, c)
        comp = Composition([
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "d", "remainder": "e"}),
            (Divmod(),
                {"left": "e", "right": "c"},
                {"quotient": "f", "remainder": "g"}),
            ])
        comp.put("a", 117)
        comp.put("b", 20)
        comp.put("c", 5)
        comp.run()
        self.assertEqual(comp.get("d"), 5)
        self.assertTrue(comp.is_status("get", "OK"))
        self.assertEqual(comp.get("f"), 3)
        self.assertTrue(comp.is_status("get", "OK"))
        self.assertEqual(comp.get("g"), 2)
        self.assertTrue(comp.is_status("get", "OK"))


class DummyNode(Node):
    def visit(self, visitor: NodeVisitor) -> None:
        pass


class Test_Node(unittest.TestCase):
    
    def test_init(self):
        d = DummyNode()
        self.assertEqual(d.get_inputs(), set())
        self.assertEqual(d.get_outputs(), set())


    def test_add_IO(self):
        d = DummyNode()
        i1 = DummyNode()
        i2 = DummyNode()
        o1 = DummyNode()
        o2 = DummyNode()
        d.add_input(i1)
        self.assertTrue(d.is_status("add_input", "OK"))
        d.add_output(o1)
        self.assertTrue(d.is_status("add_output", "OK"))
        d.add_input(i1)
        self.assertTrue(d.is_status("add_input", "ALREADY_LINKED"))
        d.add_input(o1)
        self.assertTrue(d.is_status("add_input", "ALREADY_LINKED"))
        d.add_input(i2)
        self.assertTrue(d.is_status("add_input", "OK"))
        d.add_output(o1)
        self.assertTrue(d.is_status("add_output", "ALREADY_LINKED"))
        d.add_output(i1)
        self.assertTrue(d.is_status("add_output", "ALREADY_LINKED"))
        d.add_output(o2)
        self.assertTrue(d.is_status("add_output", "OK"))
        self.assertEqual(d.get_inputs(), {i1, i2})
        self.assertEqual(d.get_outputs(), {o1, o2})


class Test_SlotNode(unittest.TestCase):
    
    def test_init(self):
        d = SlotNode("foo", int)
        self.assertEqual(d.get_inputs(), set())
        self.assertEqual(d.get_outputs(), set())
        self.assertIs(d.get_slot(), "foo")
        self.assertIs(d.get_type(), int)


class Test_ProcNode(unittest.TestCase):

    def test_init(self):
        dm = Divmod()
        p = ProcNode(dm)
        self.assertEqual(p.get_inputs(), set())
        self.assertEqual(p.get_outputs(), set())
        self.assertIs(p.get_proc(), dm)


if __name__ == "__main__":
    unittest.main()
