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


if __name__ == "__main__":
    unittest.main()
