import unittest

from solver import Calculator, Input, Output
from tools import status


class Calc(Calculator):
        
    __a: Input[int]
    __b: Input[str]
    __c: Output[int]
    __d: Output[str]

    @status()
    def calculate(self) -> None:
        a = self.__a.get()
        b = self.__b.get()
        if self.__b.get() == "exit":
            return
        if self.__b.get() == "no output":
            self._set_status("calculate", "OK")
            return
        self.__c.put(a * 2)
        self.__d.put(b + b)
        if self.__b.get() == "error":
            self._set_status("calculate", "ERROR")
            return
        self._set_status("calculate", "OK")


class Test_Calculator(unittest.TestCase):

    def test_create(self):
        s = Calc()
        self.assertEqual(s.get_input_spec(), {"a": int, "b": str})
        self.assertEqual(s.get_output_spec(), {"c": int, "d": str})

    def test_put(self):
        s = Calc()
        self.assertTrue(s.is_status("put", "NIL"))
        s.put("foo", 5)
        self.assertTrue(s.is_status("put", "INVALID_ID"))
        s.put("c", 5)
        self.assertTrue(s.is_status("put", "INVALID_ID"))
        s.put("a", "foo")
        self.assertTrue(s.is_status("put", "INVALID_VALUE"))
        s.put("a", 5)
        self.assertTrue(s.is_status("put", "OK"))
        s.put("b", "boo")
        self.assertTrue(s.is_status("put", "OK"))

    def test_run(self):
        s = Calc()
        self.assertTrue(s.is_status("run", "NIL"))
        s.run()
        self.assertTrue(s.is_status("run", "INVALID_INPUT"))
        s.put("a", 5)
        s.run()
        self.assertTrue(s.is_status("run", "INVALID_INPUT"))
        s.put("b", "exit")
        s.run()
        self.assertTrue(s.is_status("run", "INTERNAL_ERROR"))
        s.put("b", "no output")
        s.run()
        self.assertTrue(s.is_status("run", "INTERNAL_ERROR"))
        s.put("b", "error")
        s.run()
        self.assertTrue(s.is_status("run", "INTERNAL_ERROR"))
        s.put("b", "foo")
        s.run()
        self.assertTrue(s.is_status("run", "OK"))

    def test_has_value(self):
        s = Calc()
        self.assertTrue(s.is_status("has_value", "NIL"))
        s.has_value("foo")
        self.assertTrue(s.is_status("has_value", "INVALID_ID"))
        self.assertFalse(s.has_value("a"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertFalse(s.has_value("b"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertFalse(s.has_value("c"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertFalse(s.has_value("d"))
        self.assertTrue(s.is_status("has_value", "OK"))
        s.put("a", 1)
        self.assertTrue(s.has_value("a"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertFalse(s.has_value("b"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertFalse(s.has_value("c"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertFalse(s.has_value("d"))
        self.assertTrue(s.is_status("has_value", "OK"))
        s.put("b", "foo")
        self.assertTrue(s.has_value("a"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertTrue(s.has_value("b"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertFalse(s.has_value("c"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertFalse(s.has_value("d"))
        self.assertTrue(s.is_status("has_value", "OK"))
        s.run()
        self.assertTrue(s.has_value("a"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertTrue(s.has_value("b"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertTrue(s.has_value("c"))
        self.assertTrue(s.is_status("has_value", "OK"))
        self.assertTrue(s.has_value("d"))
        self.assertTrue(s.is_status("has_value", "OK"))

    def test_get(self):
        s = Calc()
        self.assertTrue(s.is_status("get", "NIL"))
        s.get("foo")
        self.assertTrue(s.is_status("get", "INVALID_ID"))
        s.get("a")
        self.assertTrue(s.is_status("get", "NO_VALUE"))
        s.get("c")
        self.assertTrue(s.is_status("get", "NO_VALUE"))
        s.put("a", 5)
        s.put("b", "foo")
        self.assertEqual(s.get("a"), 5)
        self.assertTrue(s.is_status("get", "OK"))
        self.assertEqual(s.get("b"), "foo")
        self.assertTrue(s.is_status("get", "OK"))
        s.run()
        self.assertEqual(s.get("c"), 10)
        self.assertTrue(s.is_status("get", "OK"))
        self.assertEqual(s.get("d"), "foofoo")
        self.assertTrue(s.is_status("get", "OK"))


if __name__ == "__main__":
    unittest.main()
