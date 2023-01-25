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


    def test_no_values(self):
        with self.assertRaises(AssertionError) as ae:
            class Foo(Status):
                @status()
                def stat(self) -> None:
                    pass
            Foo()
        self.assertEqual(str(ae.exception),
            "No values provided for 'stat' status of Foo")
        
        with self.assertRaises(AssertionError) as ae:
            class Boo(Status):
                @status(name="alt")
                def stat(self) -> None:
                    pass
            Boo()
        self.assertEqual(str(ae.exception),
            "No values provided for 'alt' status of Boo")


    def test_inherited(self):
        class Grand(Status):
            @status("OK", "ERR")
            def stat(self, s: str) -> None:
                self._set_status("stat", s)

            @status("OK2", "ERR2", name="alt")
            def stat2(self, s: str) -> None:
                self._set_status("alt", s)

            def no_stat(self, s: str) -> None:
                self._set_status("no_stat", s)

        class Parent(Grand):
            @status()
            def stat(self, s: str) -> None:
                self._set_status("stat", s)

            @status(name="alt")
            def stat2(self, s: str) -> None:
                self._set_status("alt", s)

            def no_stat(self, s: str) -> None:
                self._set_status("no_stat", s)

        class Child(Parent):
            @status()
            def stat(self, s: str) -> None:
                self._set_status("stat", s)

            @status(name="alt")
            def stat2(self, s: str) -> None:
                self._set_status("alt", s)

            def no_stat(self, s: str) -> None:
                self._set_status("no_stat", s)

        class Child2(Parent):
            @status("OK", "ERR")
            def stat(self, s: str) -> None:
                self._set_status("stat", s)

            @status("OK2", "ERR2", name="alt")
            def stat2(self, s: str) -> None:
                self._set_status("alt", s)

            def no_stat(self, s: str) -> None:
                self._set_status("no_stat", s)

        class Child3(Parent):
            pass

        with self.assertRaises(AssertionError) as ae:
            class Bad(Parent):
                @status("FOO")
                def stat(self, s: str) -> None:
                    self._set_status("stat", s)
            Bad()
        self.assertEqual(str(ae.exception),
            "Values for 'stat' status changed in child class Bad")

        for Foo in [Grand, Parent, Child, Child2, Child3]:
            foo = Foo()
            self.assertTrue(foo.is_status("stat", "NIL"))
            self.assertTrue(foo.is_status("alt", "NIL"))
            with self.assertRaises(AssertionError) as ae:
                foo.is_status("no_stat", "NIL")
            self.assertEqual(str(ae.exception),
                f"No 'no_stat' status for {Foo.__name__}")
            with self.assertRaises(AssertionError) as ae:
                foo.is_status("stat", "FOO")
            self.assertEqual(str(ae.exception),
                f"No 'FOO' value for 'stat' status of {Foo.__name__}")
            foo.stat("OK")
            self.assertTrue(foo.is_status("stat", "OK"))
            foo.stat("ERR")
            self.assertTrue(foo.is_status("stat", "ERR"))
            foo.stat2("OK2")
            self.assertTrue(foo.is_status("alt", "OK2"))
            foo.stat2("ERR2")
            self.assertTrue(foo.is_status("alt", "ERR2"))


if __name__ == "__main__":
    unittest.main()
