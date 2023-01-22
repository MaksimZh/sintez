import unittest

from tools import Status, status


class Test_Status(unittest.TestCase):

    def test_set_get(self):
        class Foo(Status):
            @status("OK", "ERR")
            def func(self, s: str) -> None:
                self._set_status("func", s)

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

    
    def test_instance_forbidden(self):
        self.assertRaises(TypeError, Status)

    
    def test_no_status(self):
        class Foo(Status):
            @status("OK", "ERR")
            def stat(self, s: str) -> None:
                self._set_status("stat", s)

            def no_stat(self, s: str) -> None:
                self._set_status("no_stat", s)
        
        foo = Foo()
        self.assertEqual(foo.get_status("stat"), "NIL")
        foo.stat("OK")
        self.assertEqual(foo.get_status("stat"), "OK")
        foo.stat("ERR")
        self.assertEqual(foo.get_status("stat"), "ERR")

        with self.assertRaises(AssertionError) as ae:
            foo.get_status("no_stat")
        self.assertEqual(str(ae.exception), "No 'no_stat' status for Foo")
        with self.assertRaises(AssertionError) as ae:
            foo.no_stat("OK")
        self.assertEqual(str(ae.exception), "No 'no_stat' status for Foo")



if __name__ == "__main__":
    unittest.main()
