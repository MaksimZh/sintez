import unittest

from tools import Status, status

class Foo(Status):
    @status("OK", "ERR")
    def ok(self) -> None:
        pass


class Test_Status(unittest.TestCase):

    def test(self):
        foo = Foo()
        self.assertEqual(foo.get_status("ok"), "NIL")


if __name__ == "__main__":
    unittest.main()
