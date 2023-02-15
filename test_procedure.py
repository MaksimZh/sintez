import unittest

from procedure import Slot, Calculator, Input, Output, Wrapper
from tools import status


class Test_Slot(unittest.TestCase):

    def test_init(self):
        s = Slot(int)
        self.assertIs(s.get_type(), int)
        self.assertFalse(s.has_data())

    def test_set(self):
        s = Slot(complex)
        self.assertTrue(s.is_status("set", "NIL"))
        self.assertFalse(s.has_data())
        s.set(1)
        self.assertTrue(s.is_status("set", "OK"))
        self.assertTrue(s.has_data())
        s.set(1.1)
        self.assertTrue(s.is_status("set", "OK"))
        s.set(1 + 2j)
        self.assertTrue(s.is_status("set", "OK"))
        s.set("foo")
        self.assertTrue(s.is_status("set", "INVALID_TYPE"))

    def test_clear(self):
        s = Slot(complex)
        self.assertFalse(s.has_data())
        s.set(1)
        self.assertTrue(s.has_data())
        s.clear()
        self.assertFalse(s.has_data())

    def test_get(self):
        s = Slot(int)
        self.assertTrue(s.is_status("get", "NIL"))
        s.get()
        self.assertTrue(s.is_status("get", "NO_DATA"))
        s.set(1)
        self.assertEqual(s.get(), 1)
        self.assertTrue(s.is_status("get", "OK"))


class Test_Calculator(unittest.TestCase):

    class Calc(Calculator):
        
        __a: Input[int]
        __b: Input[str]
        __c: Output[int]
        __d: Output[str]

        fail: str

        def __init__(self) -> None:
            super().__init__()
            self.fail = ""

        @status()
        def calculate(self) -> None:
            if self.fail == "exit":
                return
            if self.fail == "no output":
                self._set_status("calculate", "OK")
                return
            self.__c.set(2)
            self.__d.set("boo")
            if self.fail == "error":
                self._set_status("calculate", "ERROR")
                return
            self._set_status("calculate", "OK")


    def test_init(self):
        dm = self.Calc()
        self.assertEqual(dm.get_input_ids(), {"a", "b"})
        self.assertEqual(dm.get_output_ids(), {"c", "d"})

    def test_get_input(self):
        dm = self.Calc()
        self.assertTrue(dm.is_status("get_input", "NIL"))
        dm.get_input("foo")
        self.assertTrue(dm.is_status("get_input", "INVALID_ID"))
        dm.get_input("c")
        self.assertTrue(dm.is_status("get_input", "INVALID_ID"))
        dm.get_input("d")
        self.assertTrue(dm.is_status("get_input", "INVALID_ID"))
        a = dm.get_input("a")
        self.assertTrue(dm.is_status("get_input", "OK"))
        self.assertIsInstance(a, Slot)
        self.assertIs(a.get_type(), int)
        b = dm.get_input("b")
        self.assertTrue(dm.is_status("get_input", "OK"))
        self.assertIsInstance(b, Slot)
        self.assertIs(b.get_type(), str)

    def test_get_output(self):
        dm = self.Calc()
        self.assertTrue(dm.is_status("get_output", "NIL"))
        dm.get_output("foo")
        self.assertTrue(dm.is_status("get_output", "INVALID_ID"))
        dm.get_output("a")
        self.assertTrue(dm.is_status("get_output", "INVALID_ID"))
        dm.get_output("b")
        self.assertTrue(dm.is_status("get_output", "INVALID_ID"))
        c = dm.get_output("c")
        self.assertTrue(dm.is_status("get_output", "OK"))
        self.assertIsInstance(c, Slot)
        self.assertIs(c.get_type(), int)
        d = dm.get_output("d")
        self.assertTrue(dm.is_status("get_output", "OK"))
        self.assertIsInstance(d, Slot)
        self.assertIs(d.get_type(), str)

    def test_run(self):
        dm = self.Calc()
        a = dm.get_input("a")
        b = dm.get_input("b")
        c = dm.get_output("c")
        d = dm.get_output("d")
        self.assertTrue(dm.is_status("run", "NIL"))
        dm.run()
        self.assertTrue(dm.is_status("run", "INVALID_INPUT"))
        a.set(1)
        dm.run()
        self.assertTrue(dm.is_status("run", "INVALID_INPUT"))
        b.set("foo")
        dm.fail = "exit"
        dm.run()
        self.assertTrue(dm.is_status("run", "INTERNAL_ERROR"))
        dm.fail = "no output"
        dm.run()
        self.assertTrue(dm.is_status("run", "INTERNAL_ERROR"))
        dm.fail = ""
        dm.run()
        self.assertTrue(dm.is_status("run", "OK"))
        self.assertEqual(c.get(), 2)
        self.assertEqual(d.get(), "boo")
        dm.fail = "error"
        dm.run()
        self.assertTrue(dm.is_status("run", "INTERNAL_ERROR"))



class Test_procedure(unittest.TestCase):

    @staticmethod
    def func(a: int, b: str) -> tuple[int, str]:
        if b == "fail":
            raise ValueError()
        return 2, "boo"

    def test_init(self):
        w = Wrapper(self.func, ["c", "d"])
        self.assertEqual(w.get_input_ids(), {"a", "b"})
        self.assertEqual(w.get_output_ids(), {"c", "d"})

    def test_get_input(self):
        w = Wrapper(self.func, ["c", "d"])
        self.assertTrue(w.is_status("get_input", "NIL"))
        w.get_input("foo")
        self.assertTrue(w.is_status("get_input", "INVALID_ID"))
        w.get_input("c")
        self.assertTrue(w.is_status("get_input", "INVALID_ID"))
        w.get_input("d")
        self.assertTrue(w.is_status("get_input", "INVALID_ID"))
        a = w.get_input("a")
        self.assertTrue(w.is_status("get_input", "OK"))
        self.assertIsInstance(a, Slot)
        self.assertIs(a.get_type(), int)
        b = w.get_input("b")
        self.assertTrue(w.is_status("get_input", "OK"))
        self.assertIsInstance(b, Slot)
        self.assertIs(b.get_type(), str)

    def test_get_output(self):
        w = Wrapper(self.func, ["c", "d"])
        self.assertTrue(w.is_status("get_output", "NIL"))
        w.get_output("foo")
        self.assertTrue(w.is_status("get_output", "INVALID_ID"))
        w.get_output("a")
        self.assertTrue(w.is_status("get_output", "INVALID_ID"))
        w.get_output("b")
        self.assertTrue(w.is_status("get_output", "INVALID_ID"))
        c = w.get_output("c")
        self.assertTrue(w.is_status("get_output", "OK"))
        self.assertIsInstance(c, Slot)
        self.assertIs(c.get_type(), int)
        d = w.get_output("d")
        self.assertTrue(w.is_status("get_output", "OK"))
        self.assertIsInstance(d, Slot)
        self.assertIs(d.get_type(), str)

    def test_run(self):
        w = Wrapper(self.func, ["c", "d"])
        a = w.get_input("a")
        b = w.get_input("b")
        c = w.get_output("c")
        d = w.get_output("d")
        self.assertTrue(w.is_status("run", "NIL"))
        w.run()
        self.assertTrue(w.is_status("run", "INVALID_INPUT"))
        a.set(1)
        w.run()
        self.assertTrue(w.is_status("run", "INVALID_INPUT"))
        b.set("fail")
        w.run()
        self.assertTrue(w.is_status("run", "INTERNAL_ERROR"))
        b.set("foo")
        w.run()
        self.assertTrue(w.is_status("run", "OK"))
        self.assertEqual(c.get(), 2)
        self.assertEqual(d.get(), "boo")


if __name__ == "__main__":
    unittest.main()
