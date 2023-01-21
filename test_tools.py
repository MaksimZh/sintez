import unittest

from tools import Status, status

class Foo(Status):
    @status("OK", "ERR")
    def method(self) -> None:
        pass


class Test_Status(unittest.TestCase):

    def test(self):
        pass


if __name__ == "__main__":
    unittest.main()
