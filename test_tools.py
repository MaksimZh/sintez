import unittest

from tools import Status, status


class Test_Status(unittest.TestCase):

    def test_set_get(self):
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
        with self.assertRaises(AssertionError) as ae:
            foo.stat("FOO")
        self.assertEqual(str(ae.exception),
            "No 'FOO' value for 'stat' status of Foo")

        foo2 = Foo()
        self.assertEqual(foo2.get_status("stat"), "NIL")
        foo2.stat("OK")
        self.assertEqual(foo2.get_status("stat"), "OK")
        self.assertEqual(foo.get_status("stat"), "ERR")

    
    def test_instance_forbidden(self):
        with self.assertRaises(TypeError) as te:
            Status()
        self.assertEqual(str(te.exception),
            "Only children of Status may be instantiated")


    def test_is_status(self):
        class Foo(Status):
            @status("OK", "ERR")
            def stat(self, s: str) -> None:
                self._set_status("stat", s)

            def no_stat(self, s: str) -> None:
                self._set_status("no_stat", s)

        foo = Foo()
        self.assertTrue(foo.is_status("stat", "NIL"))
        self.assertFalse(foo.is_status("stat", "OK"))
        self.assertFalse(foo.is_status("stat", "ERR"))
        foo.stat("OK")
        self.assertFalse(foo.is_status("stat", "NIL"))
        self.assertTrue(foo.is_status("stat", "OK"))
        self.assertFalse(foo.is_status("stat", "ERR"))
        foo.stat("ERR")
        self.assertFalse(foo.is_status("stat", "NIL"))
        self.assertFalse(foo.is_status("stat", "OK"))
        self.assertTrue(foo.is_status("stat", "ERR"))

        with self.assertRaises(AssertionError) as ae:
            foo.is_status("no_stat", "NIL")
        self.assertEqual(str(ae.exception), "No 'no_stat' status for Foo")
        with self.assertRaises(AssertionError) as ae:
            foo.is_status("stat", "FOO")
        self.assertEqual(str(ae.exception),
            "No 'FOO' value for 'stat' status of Foo")


    def test_name(self):
        class Foo(Status):
            @status("OK", "ERR", name="alt")
            def stat(self, s: str) -> None:
                self._set_status("alt", s)

        foo = Foo()
        self.assertTrue(foo.is_status("alt", "NIL"))
        with self.assertRaises(AssertionError) as ae:
            foo.is_status("stat", "NIL")
        self.assertEqual(str(ae.exception), "No 'stat' status for Foo")
        foo.stat("OK")
        self.assertTrue(foo.is_status("alt", "OK"))
        foo.stat("ERR")
        self.assertTrue(foo.is_status("alt", "ERR"))

        with self.assertRaises(AssertionError) as ae:
            class Boo(Status):
                @status("OK", "ERR", name="alt")
                def stat(self, s: str) -> None:
                    self._set_status("alt", s)

                @status("OK", "ERR")
                def alt(self, s: str) -> None:
                    self._set_status("alt", s)
            Boo()
        self.assertTrue(str(ae.exception), "Duplicate status 'alt' in Boo")


if __name__ == "__main__":
    unittest.main()
