import unittest

from solver import Wrapper


class Test_Wrapper(unittest.TestCase):

    @staticmethod
    def func(a: int, b: str) -> tuple[int, str]:
        if b == "error":
            raise ValueError()
        return a * 2, b + b
    
    def test_spec(self):
        W = Wrapper(self.func, ["c", "d"])
        self.assertEqual(W.get_input_spec(), {"a": int, "b": str})
        self.assertEqual(W.get_output_spec(), {"c": int, "d": str})

    def test_create(self):
        w = Wrapper(self.func, ["c", "d"]).create()
        self.assertEqual(w.get_input_spec(), {"a": int, "b": str})
        self.assertEqual(w.get_output_spec(), {"c": int, "d": str})

    def test_put(self):
        w = Wrapper(self.func, ["c", "d"]).create()
        self.assertTrue(w.is_status("put", "NIL"))
        w.put("foo", 5)
        self.assertTrue(w.is_status("put", "INVALID_ID"))
        w.put("c", 5)
        self.assertTrue(w.is_status("put", "INVALID_ID"))
        w.put("a", "foo")
        self.assertTrue(w.is_status("put", "INVALID_VALUE"))
        w.put("a", 5)
        self.assertTrue(w.is_status("put", "OK"))
        w.put("b", "boo")
        self.assertTrue(w.is_status("put", "OK"))

    def test_run(self):
        w = Wrapper(self.func, ["c", "d"]).create()
        self.assertTrue(w.is_status("run", "NIL"))
        w.run()
        self.assertTrue(w.is_status("run", "INVALID_INPUT"))
        w.put("a", 5)
        w.run()
        self.assertTrue(w.is_status("run", "INVALID_INPUT"))
        w.put("b", "error")
        w.run()
        self.assertTrue(w.is_status("run", "INTERNAL_ERROR"))
        w.put("b", "foo")
        w.run()
        self.assertTrue(w.is_status("run", "OK"))

    def test_has_value(self):
        w = Wrapper(self.func, ["c", "d"]).create()
        self.assertTrue(w.is_status("has_value", "NIL"))
        w.has_value("foo")
        self.assertTrue(w.is_status("has_value", "INVALID_ID"))
        self.assertFalse(w.has_value("a"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertFalse(w.has_value("b"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertFalse(w.has_value("c"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertFalse(w.has_value("d"))
        self.assertTrue(w.is_status("has_value", "OK"))
        w.put("a", 1)
        self.assertTrue(w.has_value("a"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertFalse(w.has_value("b"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertFalse(w.has_value("c"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertFalse(w.has_value("d"))
        self.assertTrue(w.is_status("has_value", "OK"))
        w.put("b", "foo")
        self.assertTrue(w.has_value("a"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertTrue(w.has_value("b"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertFalse(w.has_value("c"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertFalse(w.has_value("d"))
        self.assertTrue(w.is_status("has_value", "OK"))
        w.run()
        self.assertTrue(w.has_value("a"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertTrue(w.has_value("b"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertTrue(w.has_value("c"))
        self.assertTrue(w.is_status("has_value", "OK"))
        self.assertTrue(w.has_value("d"))
        self.assertTrue(w.is_status("has_value", "OK"))

    def test_get(self):
        w = Wrapper(self.func, ["c", "d"]).create()
        self.assertTrue(w.is_status("get", "NIL"))
        w.get("foo")
        self.assertTrue(w.is_status("get", "INVALID_ID"))
        w.get("a")
        self.assertTrue(w.is_status("get", "NO_VALUE"))
        w.get("c")
        self.assertTrue(w.is_status("get", "NO_VALUE"))
        w.put("a", 5)
        w.put("b", "foo")
        self.assertEqual(w.get("a"), 5)
        self.assertTrue(w.is_status("get", "OK"))
        self.assertEqual(w.get("b"), "foo")
        self.assertTrue(w.is_status("get", "OK"))
        w.run()
        self.assertEqual(w.get("c"), 10)
        self.assertTrue(w.is_status("get", "OK"))
        self.assertEqual(w.get("d"), "foofoo")
        self.assertTrue(w.is_status("get", "OK"))


if __name__ == "__main__":
    unittest.main()
