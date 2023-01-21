import unittest

from tools import Status, status

class Foo(Status):
    @status("OK", "ERR")
    def func_ok(self) -> None:
        self._set_status("func_ok", "OK")


class Test_Status(unittest.TestCase):

    def test(self):
        foo = Foo()
        self.assertEqual(foo.get_status("func_ok"), "NIL")
        foo.func_ok()
        self.assertEqual(foo.get_status("func_ok"), "OK")


if __name__ == "__main__":
    unittest.main()
