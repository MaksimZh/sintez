import unittest

from typing import Any

from tools import status
from procedures import Calculator, Composition
from procedures import Procedure, DataNode, ProcNode


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


class Test_DataNode(unittest.TestCase):
    
    def test_init(self):
        d = DataNode(int)
        self.assertIs(d.get_type(), int)
        self.assertFalse(d.is_valid())
        self.assertIsNone(d.get_input())
        self.assertEqual(d.get_outputs(), set())


    def test_add_IO(self):
        d = DataNode(int)
        i = ProcNode(Divmod())
        o1 = ProcNode(Divmod())
        o2 = ProcNode(Divmod())
        d.add_output(o1)
        self.assertTrue(d.is_status("add_output", "OK"))
        d.add_output(o1)
        self.assertTrue(d.is_status("add_output", "ALREADY_LINKED"))
        d.add_input(o1)
        self.assertTrue(d.is_status("add_input", "ALREADY_LINKED"))
        d.add_input(i)
        self.assertTrue(d.is_status("add_input", "OK"))
        d.add_input(i)
        self.assertTrue(d.is_status("add_input", "ALREADY_LINKED"))
        d.add_input(o2)
        self.assertTrue(d.is_status("add_input", "MULTIPLE_INPUTS"))
        d.add_output(o2)
        self.assertTrue(d.is_status("add_output", "OK"))
        self.assertIs(d.get_input(), i)
        self.assertEqual(d.get_outputs(), {o1, o2})


    def test_put(self):
        d = DataNode(int)
        d.put("foo")
        self.assertTrue(d.is_status("put", "INVALID_TYPE"))
        self.assertFalse(d.is_valid())
        d.put(1)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())


    def test_invalidate(self):
        d = DataNode(int)
        d.invalidate()
        self.assertFalse(d.is_valid())
        d.put(1)
        self.assertTrue(d.is_valid())
        d.invalidate()
        self.assertFalse(d.is_valid())


    def test_get(self):
        d = DataNode(int)
        d.get()
        self.assertTrue(d.is_status("get", "INVALID_DATA"))
        d.put(1)
        self.assertEqual(d.get(), 1)
        self.assertTrue(d.is_status("get", "OK"))


class Test_ProcNode(unittest.TestCase):

    class DummyProc(Procedure):

        __input_slots: dict[str, type]
        __output_slots: dict[str, type]
        __needs_run: bool
        
        def __init__(self, inputs: dict[str, type],
                outputs: dict[str, type]) -> None:
            super().__init__()
            self.__input_slots = inputs
            self.__output_slots = outputs
            self.__needs_run = True

        @status("OK", "INVALID_SLOT", "INVALID_TYPE", "INVALID_VALUE")
        def put(self, slot: str, value: Any) -> None:
            self.__needs_run = True
            self._set_status("put", "OK")

        @status("OK", "INVALID_INPUT", "RUN_FAILED")
        def run(self) -> None:
            self.__needs_run = False
            self._set_status("run", "OK")

        def get_input_slots(self) -> dict[str, type]:
            return self.__input_slots.copy()

        def get_output_slots(self) -> dict[str, type]:
            return self.__output_slots.copy()

        def needs_run(self) -> bool:
            return self.__needs_run

        @status("OK", "INVALID_SLOT", "NEEDS_RUN")
        def get(self, slot: str) -> Any:
            self._set_status("get", "OK")
            return self.__output_slots[slot]()


    def test_init(self):
        dm = Divmod()
        p = ProcNode(dm)
        self.assertIs(p.get_proc(), dm)
        self.assertTrue(p.needs_run())
        self.assertEqual(p.get_inputs(), {})
        self.assertEqual(p.get_outputs(), {})


    def test_add_IO(self):
        p = ProcNode(self.DummyProc({"a": int, "b": str}, {"c": int, "d": str}))
        i1 = DataNode(int)
        i2 = DataNode(int)
        i3 = DataNode(str)
        o1 = DataNode(int)
        o2 = DataNode(int)
        o3 = DataNode(str)
        p.add_input("a", i1)
        self.assertTrue(p.is_status("add_input", "OK"))
        p.add_output("c", o1)
        self.assertTrue(p.is_status("add_output", "OK"))
        
        p.add_input("foo", i2)
        self.assertTrue(p.is_status("add_input", "INVALID_SLOT"))
        p.add_input("c", i2)
        self.assertTrue(p.is_status("add_input", "INVALID_SLOT"))
        p.add_input("a", i2)
        self.assertTrue(p.is_status("add_input", "SLOT_OCCUPIED"))
        p.add_input("b", i1)
        self.assertTrue(p.is_status("add_input", "ALREADY_LINKED"))
        p.add_input("b", o1)
        self.assertTrue(p.is_status("add_input", "ALREADY_LINKED"))
        p.add_input("b", i2)
        self.assertTrue(p.is_status("add_input", "INVALID_TYPE"))
        p.add_input("b", i3)
        self.assertTrue(p.is_status("add_input", "OK"))
        
        p.add_output("foo", o2)
        self.assertTrue(p.is_status("add_output", "INVALID_SLOT"))
        p.add_output("a", o2)
        self.assertTrue(p.is_status("add_output", "INVALID_SLOT"))
        p.add_output("c", o2)
        self.assertTrue(p.is_status("add_output", "SLOT_OCCUPIED"))
        p.add_output("d", o1)
        self.assertTrue(p.is_status("add_output", "ALREADY_LINKED"))
        p.add_output("d", i1)
        self.assertTrue(p.is_status("add_output", "ALREADY_LINKED"))
        p.add_output("d", o2)
        self.assertTrue(p.is_status("add_output", "INVALID_TYPE"))
        p.add_output("d", o3)
        self.assertTrue(p.is_status("add_output", "OK"))

        self.assertEqual(p.get_inputs(), {"a": i1, "b": i3})
        self.assertEqual(p.get_outputs(), {"c": o1, "d": o3})


if __name__ == "__main__":
    unittest.main()
