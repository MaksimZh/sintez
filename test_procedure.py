import unittest

from procedure import Slot, Calculator, DataSource, DataDest


class Test_Slot(unittest.TestCase):

    def test_init(self):
        s = Slot(int)
        self.assertIs(s.get_type(), int)
        self.assertEqual(s.get_state(), Slot.State.NONE)

    def test_set(self):
        s = Slot(complex)
        self.assertTrue(s.is_status("set", "NIL"))
        self.assertEqual(s.get_state(), Slot.State.NONE)
        s.set(1)
        self.assertTrue(s.is_status("set", "OK"))
        self.assertEqual(s.get_state(), Slot.State.NEW)
        s.set(1.1)
        self.assertTrue(s.is_status("set", "OK"))
        s.set(1 + 2j)
        self.assertTrue(s.is_status("set", "OK"))
        s.set("foo")
        self.assertTrue(s.is_status("set", "INVALID_TYPE"))

    def test_mark_used(self):
        s = Slot(int)
        self.assertTrue(s.is_status("mark_used", "NIL"))
        s.mark_used()
        self.assertTrue(s.is_status("mark_used", "NO_DATA"))
        s.set(1)
        s.mark_used()
        self.assertTrue(s.is_status("mark_used", "OK"))

    def test_get(self):
        s = Slot(int)
        self.assertTrue(s.is_status("get", "NIL"))
        s.get()
        self.assertTrue(s.is_status("get", "NO_DATA"))
        s.set(1)
        self.assertEqual(s.get(), 1)
        self.assertTrue(s.is_status("get", "OK"))


class Divmod(Calculator):
    
    __left: DataSource[int]
    __right: DataSource[int]
    __quotient: DataDest[int]
    __remainder: DataDest[int]


class Test_Calculator(unittest.TestCase):

    def test(self):
        pass
