import unittest
from typing import Any, Optional, final

from nodes import ValueNode, ProcedureNode, Procedure, Simulator
from nodes import DataNode, OutputData, InputProc
from tools import status


class Test_DataNode(unittest.TestCase):

    class InvalidSlotInputProc(InputProc):
   
        @status()
        def add_output(self, output: OutputData, slot: str) -> None:
            self._set_status("add_output", "INVALID_SLOT_NAME")
        
        @status()
        def validate(self) -> None:
            pass


    class InternalErrorInputProc(InputProc):
   
        @status()
        def add_output(self, output: DataNode, slot: str) -> None:
            self._set_status("add_output", "OK")
        
        @status()
        def validate(self) -> None:
            self._set_status("validate", "INTERNAL_ERROR")


    class LoggingInputProc(InputProc):

        __outputs: set[OutputData]
        __log: list[tuple[Any, ...]]

        def __init__(self) -> None:
            super().__init__()
            self.__outputs = set()
            self.reset_log()

        @status()
        def add_output(self, output: DataNode, slot: str) -> None:
            self.__outputs.add(output)
            self._set_status("add_output", "OK")
            self.__log.append(("add_output", output, slot))
        
        @status()
        def validate(self) -> None:
            for output in self.__outputs:
                output.put(0)
            self._set_status("validate", "OK")
            self.__log.append(("validate",))

        def reset_log(self) -> None:
            self.__log = []

        def get_log(self) -> list[tuple[Any, ...]]:
            return self.__log


    def test_init_no_input(self):
        d = DataNode(int)
        self.assertTrue(d.is_status("init", "OK"))


    def test_init_with_input(self):
        i = self.LoggingInputProc()
        d = DataNode(int, i, "a")
        self.assertTrue(d.is_status("init", "OK"))
        self.assertEqual(i.get_log(), [("add_output", d, "a")])


    def test_init_with_input_fail(self):
        i = self.InvalidSlotInputProc()
        d = DataNode(int, i, "a")
        self.assertTrue(d.is_status("init", "INVALID_SLOT_NAME"))


    def test_put(self):
        d = DataNode(complex)
        self.assertTrue(d.is_status("put", "NIL"))
        self.assertFalse(d.is_valid())
        d.put(1 + 2j)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())
        d.put(1.5)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())
        d.put(1)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())
        d.put("foo")
        self.assertTrue(d.is_status("put", "INCOMPATIBLE_TYPE"))
        self.assertTrue(d.is_valid())


    def test_get(self):
        d = DataNode(int)
        self.assertTrue(d.is_status("get", "NIL"))
        d.get()
        self.assertTrue(d.is_status("get", "INVALID_DATA"))
        d.put(7)
        self.assertEqual(d.get(), 7)
        self.assertTrue(d.is_status("get", "OK"))


    def test_validate_no_input(self):
        d = DataNode(int)
        self.assertTrue(d.is_status("validate", "NIL"))
        self.assertFalse(d.is_valid())
        d.validate()
        self.assertTrue(d.is_status("validate", "NO_INPUT"))
        self.assertFalse(d.is_valid())
        d.put(7)
        self.assertTrue(d.is_valid())
        d.validate()
        self.assertTrue(d.is_status("validate", "OK"))
        self.assertTrue(d.is_valid())


    def test_validate_with_input_fail(self):
        i = self.InternalErrorInputProc()
        d = DataNode(int, i, "a")
        self.assertTrue(d.is_status("validate", "NIL"))
        self.assertFalse(d.is_valid())
        d.validate()
        self.assertTrue(d.is_status("validate", "INPUT_FAILED"))
        self.assertFalse(d.is_valid())
        d.put(7)
        self.assertTrue(d.is_valid())
        d.validate()
        self.assertTrue(d.is_status("validate", "OK"))
        self.assertTrue(d.is_valid())


    def test_validate_with_input(self):
        i = self.LoggingInputProc()
        d = DataNode(int, i, "a")
        self.assertTrue(d.is_status("validate", "NIL"))
        self.assertFalse(d.is_valid())
        i.reset_log()
        d.validate()
        self.assertTrue(d.is_status("validate", "OK"))
        self.assertEqual(i.get_log(), [("validate",)])
        self.assertTrue(d.is_valid())
        self.assertEqual(d.get(), 0)


class BlackHole(Procedure):
    
    @final
    @status()
    def put(self, name: str, value: Any) -> None:
        self._set_status("put", "OK")
    
    @final
    @status()
    def get(self, name: str) -> Any:
        self._set_status("get", "OK")
        return 0


class WhiteHole(Procedure):
    
    @final
    @status()
    def put(self, name: str, value: Any) -> None:
        self._set_status("put", "INTERNAL_ERROR")

    
    @final
    @status()
    def get(self, name: str) -> Any:
        self._set_status("get", "INTERNAL_ERROR")


class LoggingProc(Procedure):

    __log: list[tuple[str, str]]

    def __init__(self) -> None:
        super().__init__()
        self.__log = []
    
    @final
    @status()
    def put(self, name: str, value: Any) -> None:
        self._set_status("put", "OK")
        self.__log.append(("put", name))
    
    @final
    @status()
    def get(self, name: str) -> Any:
        self._set_status("get", "OK")
        self.__log.append(("get", name))
        return 0

    def get_log(self) -> list[tuple[str, str]]:
        return self.__log


class Divmod(Procedure):
    
    __left: Optional[int]
    __right: Optional[int]
    __need_calculate: bool
    __quotient: Optional[int]
    __remainder: Optional[int]

    def __init__(self) -> None:
        super().__init__()
        self.__left = None
        self.__right = None
        self.__quotient = None
        self.__remainder = None
        self.__need_calculate = True

    @final
    @status()
    def put(self, name: str, value: Any) -> None:
        if type(value) is not int:
            self._set_status("put", "INCOMPATIBLE_TYPE")
            return
        self.__need_calculate = True
        match name:
            case "left":
                self.__left = value
                self._set_status("put", "OK")
            case "right":
                self.__right = value
                self._set_status("put", "OK")
            case _:
                self._set_status("put", "INVALID_NAME")
    
    @final
    @status()
    def get(self, name: str) -> Any:
        if self.__left is None or self.__right is None:
            self._set_status("get", "INCOMPLETE_INPUT")
            return None
        if self.__need_calculate:
            self.__quotient, self.__remainder = divmod(self.__left, self.__right)
        match name:
            case "quotient":
                self._set_status("get", "OK")
                return self.__quotient
            case "remainder":
                self._set_status("get", "OK")
                return self.__remainder
            case _:
                self._set_status("get", "INVALID_NAME")
                return None


class Test_ValueNode(unittest.TestCase):

    def test_build(self):
        v = ValueNode(int)
        p1 = ProcedureNode(WhiteHole())
        p2 = ProcedureNode(WhiteHole())
        p3 = ProcedureNode(WhiteHole())
        p4 = ProcedureNode(WhiteHole())
        self.assertTrue(v.is_status("add_input", "NIL"))
        self.assertTrue(v.is_status("add_output", "NIL"))
        self.assertIsNone(v.get_input())
        self.assertEqual(v.get_outputs(), set())
        v.add_output(p2)
        self.assertTrue(v.is_status("add_output", "OK"))
        v.add_output(p2)
        self.assertTrue(v.is_status("add_output", "ALREADY_LINKED"))
        v.add_input(p2)
        self.assertTrue(v.is_status("add_input", "ALREADY_LINKED"))
        v.add_input(p1)
        self.assertTrue(v.is_status("add_input", "OK"))
        v.add_input(p1)
        self.assertTrue(v.is_status("add_input", "ALREADY_LINKED"))
        v.add_input(p3)
        self.assertTrue(v.is_status("add_input", "TOO_MANY_INPUTS"))
        v.add_output(p1)
        self.assertTrue(v.is_status("add_output", "ALREADY_LINKED"))
        v.add_output(p3)
        self.assertTrue(v.is_status("add_output", "OK"))
        self.assertEqual(v.get_input(), p1)
        self.assertEqual(v.get_outputs(), {p2, p3})
        v.complete_build()
        v.add_input(p4)
        self.assertTrue(v.is_status("add_input", "BUILD_COMPLETE"))
        v.add_output(p4)
        self.assertTrue(v.is_status("add_output", "BUILD_COMPLETE"))
        self.assertEqual(v.get_input(), p1)
        self.assertEqual(v.get_outputs(), {p2, p3})


    def test_is_valid(self):
        v = ValueNode(int)
        self.assertTrue(v.is_status("is_valid", "NIL"))
        v.is_valid()
        self.assertTrue(v.is_status("is_valid", "BUILD_INCOMPLETE"))
        v.complete_build()
        self.assertFalse(v.is_valid())
        self.assertTrue(v.is_status("is_valid", "OK"))


    def test_put_last(self):
        v = ValueNode(float)
        self.assertTrue(v.is_status("put", "NIL"))
        v.put(1)
        self.assertTrue(v.is_status("put", "BUILD_INCOMPLETE"))
        v.complete_build()
        self.assertFalse(v.is_valid())
        v.put("foo")
        self.assertTrue(v.is_status("put", "INCOMPATIBLE_TYPE"))
        self.assertFalse(v.is_valid())
        v.put(1)
        self.assertTrue(v.is_status("put", "OK"))
        self.assertTrue(v.is_valid())
        v.put(0.5)
        self.assertTrue(v.is_status("put", "OK"))
        self.assertTrue(v.is_valid())


    def test_put_mid(self):
        v = ValueNode(float)
        p = ProcedureNode(WhiteHole())
        v.add_output(p)
        p.add_input("a", v)
        p.complete_build()
        self.assertTrue(v.is_status("put", "NIL"))
        v.put(1)
        self.assertTrue(v.is_status("put", "BUILD_INCOMPLETE"))
        v.complete_build()
        self.assertFalse(v.is_valid())
        self.assertTrue(p.is_status("invalidate", "NIL"))
        v.put("foo")
        self.assertTrue(v.is_status("put", "INCOMPATIBLE_TYPE"))
        self.assertFalse(v.is_valid())
        self.assertTrue(p.is_status("invalidate", "NIL"))
        v.put(1)
        self.assertTrue(v.is_status("put", "OK"))
        self.assertTrue(v.is_valid())
        self.assertTrue(p.is_status("invalidate", "OK"))
        v.put(0.5)
        self.assertTrue(v.is_status("put", "OK"))
        self.assertTrue(v.is_valid())
        self.assertTrue(p.is_status("invalidate", "OK"))


    def test_invalidate(self):
        v = ValueNode(int)
        p = ProcedureNode(WhiteHole())
        v.add_output(p)
        p.add_input("a", v)
        p.complete_build()
        self.assertTrue(v.is_status("invalidate", "NIL"))
        v.invalidate()
        self.assertTrue(v.is_status("invalidate", "BUILD_INCOMPLETE"))
        v.complete_build()
        self.assertFalse(v.is_valid())
        self.assertTrue(p.is_status("invalidate", "NIL"))
        v.invalidate()
        self.assertTrue(v.is_status("invalidate", "OK"))
        self.assertFalse(v.is_valid())
        self.assertTrue(p.is_status("invalidate", "NIL"))
        v.put(1)
        self.assertTrue(v.is_valid())
        v.invalidate()
        self.assertTrue(v.is_status("invalidate", "OK"))
        self.assertFalse(v.is_valid())
        self.assertTrue(p.is_status("invalidate", "OK"))


    def test_validate_first(self):
        v = ValueNode(int)
        self.assertTrue(v.is_status("validate", "NIL"))
        v.validate()
        self.assertTrue(v.is_status("validate", "BUILD_INCOMPLETE"))
        v.complete_build()
        v.validate()
        self.assertTrue(v.is_status("validate", "NO_VALUE_SOURCE"))
        v.put(1)
        v.validate()
        self.assertTrue(v.is_status("validate", "OK"))


    def test_validate_mid_fail(self):
        v = ValueNode(int)
        p = ProcedureNode(WhiteHole())
        v.add_input(p)
        p.add_output("a", v)
        p.complete_build()
        self.assertTrue(v.is_status("validate", "NIL"))
        v.validate()
        self.assertTrue(v.is_status("validate", "BUILD_INCOMPLETE"))
        v.complete_build()
        self.assertTrue(p.is_status("validate", "NIL"))
        v.validate()
        self.assertTrue(v.is_status("validate", "INPUT_FAILED"))
        self.assertTrue(p.is_status("validate", "FAIL"))


    def test_validate_mid_success(self):
        v = ValueNode(int)
        p = ProcedureNode(BlackHole())
        v.add_input(p)
        p.add_output("a", v)
        p.complete_build()
        v.complete_build()
        self.assertTrue(p.is_status("validate", "NIL"))
        v.validate()
        self.assertTrue(v.is_status("validate", "OK"))
        self.assertTrue(p.is_status("validate", "OK"))


    def test_get_type(self):
        v1 = ValueNode(int)
        v2 = ValueNode(str)
        self.assertIs(v1.get_type(), int)
        self.assertIs(v2.get_type(), str)


    def test_get(self):
        v = ValueNode(int)
        self.assertTrue(v.is_status("get", "NIL"))
        v.get()
        self.assertTrue(v.is_status("get", "BUILD_INCOMPLETE"))
        v.complete_build()
        v.get()
        self.assertTrue(v.is_status("get", "INVALID_VALUE"))
        v.put(1)
        self.assertEqual(v.get(), 1)
        self.assertTrue(v.is_status("get", "OK"))


class Test_ProcNode(unittest.TestCase):

    def test_build(self):
        p = ProcedureNode(WhiteHole())
        v1 = ValueNode(int)
        v2 = ValueNode(int)
        v3 = ValueNode(int)
        v4 = ValueNode(int)
        v5 = ValueNode(int)
        self.assertTrue(p.is_status("add_input", "NIL"))
        self.assertTrue(p.is_status("add_output", "NIL"))
        self.assertEqual(p.get_inputs(), dict())
        self.assertEqual(p.get_outputs(), dict())
        p.add_input("a", v1)
        self.assertTrue(p.is_status("add_input", "OK"))
        p.add_input("a", v1)
        self.assertTrue(p.is_status("add_input", "ALREADY_LINKED"))
        p.add_input("a", v2)
        self.assertTrue(p.is_status("add_input", "DUPLICATE_NAME"))
        p.add_input("b", v2)
        self.assertTrue(p.is_status("add_input", "OK"))
        p.add_output("c", v1)
        self.assertTrue(p.is_status("add_output", "ALREADY_LINKED"))
        p.add_output("a", v3)
        self.assertTrue(p.is_status("add_output", "DUPLICATE_NAME"))
        p.add_output("c", v3)
        self.assertTrue(p.is_status("add_output", "OK"))
        p.add_input("d", v3)
        self.assertTrue(p.is_status("add_input", "ALREADY_LINKED"))
        p.add_input("c", v4)
        self.assertTrue(p.is_status("add_input", "DUPLICATE_NAME"))
        p.add_output("d", v4)
        self.assertTrue(p.is_status("add_output", "OK"))
        self.assertEqual(p.get_inputs(), {"a": v1, "b": v2})
        self.assertEqual(p.get_outputs(), {"c": v3, "d": v4})
        p.complete_build()
        p.add_input("e", v5)
        self.assertTrue(p.is_status("add_input", "BUILD_COMPLETE"))
        p.add_output("e", v5)
        self.assertTrue(p.is_status("add_output", "BUILD_COMPLETE"))
        self.assertEqual(p.get_inputs(), {"a": v1, "b": v2})
        self.assertEqual(p.get_outputs(), {"c": v3, "d": v4})


    def test_invalidate(self):
        i1 = ValueNode(int)
        v2 = ValueNode(int)
        p = ProcedureNode(WhiteHole())
        o1 = ValueNode(int)
        o2 = ValueNode(int)
        p.add_input("a", i1)
        p.add_output("b", o1)
        p.add_output("c", o2)
        o1.complete_build()
        o2.complete_build()
        self.assertTrue(p.is_status("invalidate", "NIL"))
        p.invalidate(i1)
        self.assertTrue(p.is_status("invalidate", "BUILD_INCOMPLETE"))
        p.complete_build()
        p.invalidate(v2)
        self.assertTrue(p.is_status("invalidate", "NOT_INPUT"))
        self.assertTrue(o1.is_status("invalidate", "NIL"))
        self.assertTrue(o2.is_status("invalidate", "NIL"))
        p.invalidate(i1)
        self.assertTrue(p.is_status("invalidate", "OK"))
        self.assertTrue(o1.is_status("invalidate", "OK"))
        self.assertTrue(o2.is_status("invalidate", "OK"))


    def test_validate_fail(self):
        p = ProcedureNode(WhiteHole())
        i1 = ValueNode(int)
        i2 = ValueNode(int)
        o1 = ValueNode(int)
        o2 = ValueNode(int)
        p.add_input("a", i1)
        p.add_input("b", i2)
        p.add_output("c", o1)
        p.add_output("d", o2)
        i1.add_output(p)
        i2.add_output(p)
        i1.complete_build()
        i2.complete_build()
        o1.complete_build()
        o2.complete_build()
        self.assertTrue(p.is_status("validate", "NIL"))
        self.assertTrue(i1.is_status("validate", "NIL"))
        self.assertTrue(i2.is_status("validate", "NIL"))
        self.assertTrue(i1.is_status("get", "NIL"))
        self.assertTrue(i2.is_status("get", "NIL"))
        p.validate()
        self.assertTrue(p.is_status("validate", "BUILD_INCOMPLETE"))
        self.assertTrue(i1.is_status("validate", "NIL"))
        self.assertTrue(i2.is_status("validate", "NIL"))
        self.assertTrue(i1.is_status("get", "NIL"))
        self.assertTrue(i2.is_status("get", "NIL"))
        p.complete_build()
        p.validate()
        self.assertTrue(p.is_status("validate", "INPUT_VALIDATION_FAILED"))
        self.assertTrue(i1.is_status("get", "NIL"))
        self.assertTrue(i2.is_status("get", "NIL"))
        i1.put(1)
        i2.put(2)
        self.assertTrue(i1.is_status("get", "NIL"))
        self.assertTrue(i2.is_status("get", "NIL"))
        self.assertTrue(o1.is_status("put", "NIL"))
        self.assertTrue(o2.is_status("put", "NIL"))
        p.validate()
        self.assertTrue(p.is_status("validate", "FAIL"))
        self.assertTrue(i1.is_status("validate", "OK"))
        self.assertTrue(i2.is_status("validate", "OK"))
        self.assertTrue(o1.is_status("put", "NIL"))
        self.assertTrue(o2.is_status("put", "NIL"))


    def test_validate_success(self):
        proc = LoggingProc()
        p = ProcedureNode(proc)
        i1 = ValueNode(int)
        i2 = ValueNode(int)
        o1 = ValueNode(int)
        o2 = ValueNode(int)
        p.add_input("a", i1)
        p.add_input("b", i2)
        p.add_output("c", o1)
        p.add_output("d", o2)
        i1.add_output(p)
        i2.add_output(p)
        i1.complete_build()
        i2.complete_build()
        o1.complete_build()
        o2.complete_build()
        p.complete_build()
        i1.put(1)
        i2.put(2)
        self.assertTrue(o1.is_status("put", "NIL"))
        self.assertTrue(o2.is_status("put", "NIL"))
        p.validate()
        self.assertTrue(p.is_status("validate", "OK"))
        self.assertTrue(i1.is_status("validate", "OK"))
        self.assertTrue(i2.is_status("validate", "OK"))
        self.assertTrue(i1.is_status("get", "OK"))
        self.assertTrue(i2.is_status("get", "OK"))
        self.assertTrue(o1.is_status("put", "OK"))
        self.assertTrue(o2.is_status("put", "OK"))
        log = proc.get_log()
        self.assertEqual(len(log), 4)
        self.assertEqual(set(log[0:2]), {("put", "a"), ("put", "b")})
        self.assertEqual(set(log[2:4]), {("get", "c"), ("get", "d")})
        i2.put(3)
        p.validate()
        self.assertTrue(p.is_status("validate", "OK"))
        self.assertTrue(i1.is_status("validate", "OK"))
        self.assertTrue(i2.is_status("validate", "OK"))
        self.assertTrue(i2.is_status("get", "OK"))
        self.assertTrue(o1.is_status("put", "OK"))
        self.assertTrue(o2.is_status("put", "OK"))
        log = proc.get_log()[4:]
        self.assertEqual(len(log), 3)
        self.assertEqual(log[0], ("put", "b"))
        self.assertEqual(set(log[1:3]), {("get", "c"), ("get", "d")})


class Test_Nodes(unittest.TestCase):

    def test_single(self):
        a = ValueNode(int)
        b = ValueNode(int)
        q = ValueNode(int)
        r = ValueNode(int)
        dm = ProcedureNode(Divmod())
        a.add_output(dm)
        a.complete_build()
        b.add_output(dm)
        b.complete_build()
        dm.add_input("left", a)
        dm.add_input("right", b)
        dm.add_output("quotient", q)
        dm.add_output("remainder", r)
        dm.complete_build()
        q.add_input(dm)
        q.complete_build()
        r.add_input(dm)
        r.complete_build()
        a.put(20)
        b.put(7)
        q.validate()
        r.validate()
        self.assertEqual(q.get(), 2)
        self.assertEqual(r.get(), 6)

    def test_chain(self):
        a = ValueNode(int)
        b = ValueNode(int)
        c = ValueNode(int)
        d = ValueNode(int)
        e = ValueNode(int)
        f = ValueNode(int)
        p1 = ProcedureNode(Divmod())
        p2 = ProcedureNode(Divmod())
        a.add_output(p1)
        a.complete_build()
        b.add_output(p1)
        b.complete_build()
        p1.add_input("left", a)
        p1.add_input("right", b)
        p1.add_output("quotient", c)
        p1.add_output("remainder", d)
        p1.complete_build()
        c.add_input(p1)
        c.add_output(p2)
        c.complete_build()
        d.add_input(p1)
        d.add_output(p2)
        d.complete_build()
        p2.add_input("left", c)
        p2.add_input("right", d)
        p2.add_output("quotient", e)
        p2.add_output("remainder", f)
        p2.complete_build()
        e.add_input(p2)
        e.complete_build()
        f.add_input(p2)
        f.complete_build()
        a.put(101)
        b.put(7)
        e.validate()
        f.validate()
        self.assertEqual(e.get(), 4)
        self.assertEqual(f.get(), 2)


class Test_Simulator(unittest.TestCase):

    def test_init(self):
        s = Simulator([
            ("a", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            ("a", int),
            ("b", int),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            ("a", int),
            ("b", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": "e", "remainder": "f"}),
            ("e", int),
            ("f", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            (Divmod(),
                {"left": int, "right": int},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": int, "remainder": int}),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {"foo": int}, {}),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {}, {"foo": int}),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            ("a", int),
            ("b", int),
            ("a", str),
        ])
        self.assertTrue(s.is_status("init", "DUPLICATE_NAME"))
        self.assertEqual(s.get_init_message(), "Duplicate name: 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"left": "c"},
                {}),
        ])
        self.assertTrue(s.is_status("init", "NAME_NOT_FOUND"))
        self.assertEqual(s.get_init_message(), "Input not found: 'left': 'c'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {},
                {"left": "c"}),
        ])
        self.assertTrue(s.is_status("init", "NAME_NOT_FOUND"))
        self.assertEqual(s.get_init_message(), "Output not found: 'left': 'c'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"foo": "a", "boo": "a"},
                {}),
        ])
        self.assertTrue(s.is_status("init", "ALREADY_LINKED"))
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"foo": "a"},
                {"boo": "a"}),
        ])
        self.assertTrue(s.is_status("init", "ALREADY_LINKED"))
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {},
                {"foo": "a", "boo": "a"}),
        ])
        self.assertTrue(s.is_status("init", "ALREADY_LINKED"))
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(), {}, {"foo": "a"}),
            (BlackHole(), {}, {"foo": "a"}),
        ])
        self.assertTrue(s.is_status("init", "TOO_MANY_INPUTS"))
        self.assertEqual(s.get_init_message(), "Too many inputs: 'foo': 'a'")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {"foo": str}, {}),
        ])
        self.assertTrue(s.is_status("init", "AUTO_VALUE_TYPE_MISMATCH"))
        self.assertEqual(s.get_init_message(),
            "Auto value 'foo' type mismatch: <class 'str'> and <class 'int'>")


    def test_put(self):
        s = Simulator([("a", int), ("a", int)])
        self.assertTrue(s.is_status("init", "DUPLICATE_NAME"))
        self.assertTrue(s.is_status("put", "NIL"))
        s.put("a", 1)
        self.assertTrue(s.is_status("put", "INTERNAL_ERROR"))

        s = Simulator([
            ("a", int),
            ("b", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": "e", "remainder": "f"}),
            ("e", int),
            ("f", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertTrue(s.is_status("put", "NIL"))
        s.put("a", 1)
        self.assertTrue(s.is_status("put", "OK"))
        s.put("foo", 1)
        self.assertTrue(s.is_status("put", "INVALID_NAME"))
        s.put("c", 1)
        self.assertTrue(s.is_status("put", "INVALID_NAME"))


    def test_get(self):
        s = Simulator([("a", int), ("a", int)])
        self.assertTrue(s.is_status("init", "DUPLICATE_NAME"))
        self.assertTrue(s.is_status("get", "NIL"))
        s.get("a")
        self.assertTrue(s.is_status("get", "INTERNAL_ERROR"))

        s = Simulator([
            ("a", int),
            ("b", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": "e", "remainder": "f"}),
            ("e", int),
            ("f", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertTrue(s.is_status("get", "NIL"))
        s.get("foo")
        self.assertTrue(s.is_status("get", "INVALID_NAME"))
        s.get("e")
        self.assertTrue(s.is_status("get", "INCOMPLETE_INPUT"))
        s.put("a", 101)
        s.put("b", 7)
        self.assertEqual(s.get("e"), 4)
        self.assertTrue(s.is_status("get", "OK"))
        self.assertEqual(s.get("c"), 14)
        self.assertTrue(s.is_status("get", "OK"))


    def test_Nested(self):
        ddm = Simulator([
            ("a", int),
            ("b", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": "e", "remainder": "f"}),
            ("e", int),
            ("f", int),
        ])
        s = Simulator([
            ("a", int),
            ("b", int),
            (ddm,
                {"a": "a", "b": "b"},
                {"e": "c", "f": "d"}),
            ("c", int),
            ("d", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        s.put("a", 101)
        s.put("b", 7)
        self.assertEqual(s.get("c"), 4)
        self.assertTrue(s.is_status("get", "OK"))
        self.assertEqual(s.get("d"), 2)
        self.assertTrue(s.is_status("get", "OK"))


if __name__ == "__main__":
    unittest.main()
