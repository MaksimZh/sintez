import unittest

from typing import Any

from tools import status
from procedures import Calculator, Composition


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
        dm.set("left", 101)
        self.assertTrue(dm.is_status("set", "OK"))
        dm.set("middle", 1)
        self.assertTrue(dm.is_status("set", "INVALID_SLOT"))
        dm.set("quotient", 1)
        self.assertTrue(dm.is_status("set", "INVALID_SLOT"))
        dm.set("right", "foo")
        self.assertTrue(dm.is_status("set", "INVALID_TYPE"))
        dm.set("right", 0)
        self.assertTrue(dm.is_status("set", "INVALID_VALUE"))
        dm.set("right", 7)
        self.assertTrue(dm.is_status("set", "OK"))
        dm.set("left", 42)
        self.assertTrue(dm.is_status("set", "OK"))
        dm.set("right", 17)
        self.assertTrue(dm.is_status("set", "OK"))


    def test_run_success(self):
        dm = Divmod()
        self.assertTrue(dm.needs_run())
        dm.set("left", 101)
        dm.set("right", 7)
        self.assertTrue(dm.needs_run())
        dm.run()
        self.assertTrue(dm.is_status("run", "OK"))
        self.assertFalse(dm.needs_run())
        dm.set("left", 11)
        self.assertTrue(dm.needs_run())
        dm.run()
        self.assertTrue(dm.is_status("run", "OK"))
        self.assertFalse(dm.needs_run())


    def test_run_missing_input(self):
        dm = Divmod()
        dm.set("left", 101)
        dm.run()
        self.assertTrue(dm.is_status("run", "INVALID_INPUT"))
        self.assertTrue(dm.needs_run())


    def test_run_fail(self):
        dm = Divmod()
        dm.set("left", 101)
        dm.set("right", -7)
        dm.run()
        self.assertTrue(dm.is_status("run", "RUN_FAILED"))
        self.assertTrue(dm.needs_run())


    def test_get(self):
        dm = Divmod()
        dm.set("left", 101)
        dm.set("right", 7)
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
        comp.set("a", 101)
        self.assertTrue(comp.is_status("set", "OK"))
        comp.set("foo", 101)
        self.assertTrue(comp.is_status("set", "INVALID_SLOT"))
        comp.set("e", 101)
        self.assertTrue(comp.is_status("set", "INVALID_SLOT"))
        comp.set("quotient", 101)
        self.assertTrue(comp.is_status("set", "INVALID_SLOT"))
        comp.set("f", 101)
        self.assertTrue(comp.is_status("set", "INVALID_SLOT"))
        comp.set("a", "foo")
        self.assertTrue(comp.is_status("set", "INVALID_TYPE"))
        comp.set("b", 0)
        self.assertTrue(comp.is_status("set", "INVALID_VALUE"))
        comp.set("b", 7)
        self.assertTrue(comp.is_status("set", "OK"))
        comp.set("c", 3)
        self.assertTrue(comp.is_status("set", "OK"))
        comp.set("a", 101)
        self.assertTrue(comp.is_status("set", "OK"))
        comp.set("b", 17)
        self.assertTrue(comp.is_status("set", "OK"))
        comp.set("c", 13)
        self.assertTrue(comp.is_status("set", "OK"))


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
        comp.set("a", 117)
        comp.set("b", 20)
        comp.set("c", 5)
        self.assertTrue(comp.needs_run())
        comp.run()
        self.assertTrue(comp.is_status("run", "OK"))
        self.assertFalse(comp.needs_run())
        comp.set("b", 40)
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
        comp.set("a", 117)
        comp.set("b", 20)
        comp.set("c", 5)
        comp.run()
        #self.assertEqual(comp.get("d"), 17)
        #self.assertTrue(comp.is_status("get", "OK"))


if __name__ == "__main__":
    unittest.main()
