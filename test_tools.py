import unittest

from tools import Status, status

class Foo(Status):
    @status("OK", "ERR")
    def func(self, s: str) -> None:
        self._set_status("func", s)


class Test_Status(unittest.TestCase):

    def test_set_get(self):
        foo = Foo()
        self.assertEqual(foo.get_status("func"), "NIL")
        foo.func("OK")
        self.assertEqual(foo.get_status("func"), "OK")
        foo.func("ERR")
        self.assertEqual(foo.get_status("func"), "ERR")

        foo2 = Foo()
        self.assertEqual(foo2.get_status("func"), "NIL")
        foo2.func("OK")
        self.assertEqual(foo2.get_status("func"), "OK")
        self.assertEqual(foo.get_status("func"), "ERR")

    
    def test_instance(self):
        self.assertRaises(TypeError, Status)


if __name__ == "__main__":
    unittest.main()
