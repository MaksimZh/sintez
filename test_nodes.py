import unittest
from typing import Any, Optional

from nodes import ValueNode, ProcedureNode, Procedure, Simulator


class BlackHole(Procedure):
    
    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.OK
    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.OK
        return 0


class WhiteHole(Procedure):
    
    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.INTERNAL_ERROR

    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.INTERNAL_ERROR



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

    def put(self, name: str, value: Any) -> None:
        if type(value) is not int:
            self._put_status = self.PutStatus.INCOMPATIBLE_TYPE
            return
        self.__need_calculate = True
        match name:
            case "left":
                self.__left = value
                self._put_status = self.PutStatus.OK
            case "right":
                self.__right = value
                self._put_status = self.PutStatus.OK
            case _:
                self._put_status = self.PutStatus.INVALID_NAME
    
    def get(self, name: str) -> Any:
        if self.__left is None or self.__right is None:
            self._get_status = self.GetStatus.INCOMPLETE_INPUT
            return None
        if self.__need_calculate:
            self.__quotient, self.__remainder = divmod(self.__left, self.__right)
        match name:
            case "quotient":
                self._get_status = self.GetStatus.OK
                return self.__quotient
            case "remainder":
                self._get_status = self.GetStatus.OK
                return self.__remainder
            case _:
                self._get_status = self.GetStatus.INVALID_NAME
                return None


class Test_ValueNode(unittest.TestCase):

    def test_build(self):
        v = ValueNode(int)
        p1 = ProcedureNode(WhiteHole())
        p2 = ProcedureNode(WhiteHole())
        p3 = ProcedureNode(WhiteHole())
        p4 = ProcedureNode(WhiteHole())
        self.assertEqual(v.get_add_input_status(), ValueNode.AddInputStatus.NIL)
        self.assertEqual(v.get_add_output_status(), ValueNode.AddOutputStatus.NIL)
        self.assertIsNone(v.get_input())
        self.assertEqual(v.get_outputs(), set())
        v.add_output(p2)
        self.assertEqual(v.get_add_output_status(), ValueNode.AddOutputStatus.OK)
        v.add_output(p2)
        self.assertEqual(v.get_add_output_status(), ValueNode.AddOutputStatus.ALREADY_LINKED)
        v.add_input(p2)
        self.assertEqual(v.get_add_input_status(), ValueNode.AddInputStatus.ALREADY_LINKED)
        v.add_input(p1)
        self.assertEqual(v.get_add_input_status(), ValueNode.AddInputStatus.OK)
        v.add_input(p1)
        self.assertEqual(v.get_add_input_status(), ValueNode.AddInputStatus.ALREADY_LINKED)
        v.add_input(p3)
        self.assertEqual(v.get_add_input_status(), ValueNode.AddInputStatus.TOO_MANY_INPUTS)
        v.add_output(p1)
        self.assertEqual(v.get_add_output_status(), ValueNode.AddOutputStatus.ALREADY_LINKED)
        v.add_output(p3)
        self.assertEqual(v.get_add_output_status(), ValueNode.AddOutputStatus.OK)
        self.assertEqual(v.get_input(), p1)
        self.assertEqual(v.get_outputs(), {p2, p3})
        v.complete_build()
        v.add_input(p4)
        self.assertEqual(v.get_add_input_status(), ValueNode.AddInputStatus.BUILD_COMPLETE)
        v.add_output(p4)
        self.assertEqual(v.get_add_output_status(), ValueNode.AddOutputStatus.BUILD_COMPLETE)
        self.assertEqual(v.get_input(), p1)
        self.assertEqual(v.get_outputs(), {p2, p3})


    def test_get_state(self):
        v = ValueNode(int)
        self.assertEqual(v.get_get_state_status(), ValueNode.GetStateStatus.NIL)
        v.get_state()
        self.assertEqual(v.get_get_state_status(), ValueNode.GetStateStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(v.get_get_state_status(), ValueNode.GetStateStatus.OK)


    def test_put_last(self):
        v = ValueNode(float)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        v.put("foo")
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.INCOMPATIBLE_TYPE)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.REGULAR)
        v.put(0.5)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.REGULAR)


    def test_put_mid(self):
        v = ValueNode(float)
        p = ProcedureNode(WhiteHole())
        v.add_output(p)
        p.complete_build()
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.NIL)
        v.put("foo")
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.INCOMPATIBLE_TYPE)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.OK)
        v.put(0.5)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.OK)


    def test_invalidate(self):
        v = ValueNode(int)
        p = ProcedureNode(WhiteHole())
        v.add_output(p)
        p.complete_build()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.NIL)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.NIL)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.OK)


    def test_used(self):
        v = ValueNode(int)
        p1 = ProcedureNode(WhiteHole())
        p2 = ProcedureNode(WhiteHole())
        p3 = ProcedureNode(WhiteHole())
        v.add_output(p1)
        v.add_output(p2)
        p1.complete_build()
        p2.complete_build()
        p3.complete_build()
        self.assertEqual(v.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        v.used_by(p1)
        self.assertEqual(v.get_used_by_status(), ValueNode.UsedByStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        v.used_by(p1)
        self.assertEqual(v.get_used_by_status(), ValueNode.UsedByStatus.INVALID_VALUE)
        v.put(1)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        v.used_by(p1)
        self.assertEqual(v.get_used_by_status(), ValueNode.UsedByStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        v.used_by(p3)
        self.assertEqual(v.get_used_by_status(), ValueNode.UsedByStatus.NOT_OUTPUT)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        v.used_by(p2)
        self.assertEqual(v.get_used_by_status(), ValueNode.UsedByStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.REGULAR)


    def test_validate_first(self):
        v = ValueNode(int)
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.BUILD_INCOMPLETE)
        v.complete_build()
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.NO_VALUE_SOURCE)
        v.put(1)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.OK)


    def test_validate_mid_fail(self):
        v = ValueNode(int)
        p = ProcedureNode(WhiteHole())
        v.add_input(p)
        p.add_output("a", v)
        p.complete_build()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.INPUT_FAILED)
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.FAIL)


    def test_validate_mid_success(self):
        v = ValueNode(int)
        p = ProcedureNode(BlackHole())
        v.add_input(p)
        p.add_output("a", v)
        p.complete_build()
        v.complete_build()
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.OK)


    def test_get_type(self):
        v1 = ValueNode(int)
        v2 = ValueNode(str)
        self.assertIs(v1.get_type(), int)
        self.assertIs(v2.get_type(), str)


    def test_get(self):
        v = ValueNode(int)
        self.assertEqual(v.get_get_status(), ValueNode.GetStatus.NIL)
        v.get()
        self.assertEqual(v.get_get_status(), ValueNode.GetStatus.BUILD_INCOMPLETE)
        v.complete_build()
        v.get()
        self.assertEqual(v.get_get_status(), ValueNode.GetStatus.INVALID_VALUE)
        v.put(1)
        self.assertEqual(v.get(), 1)
        self.assertEqual(v.get_get_status(), ValueNode.GetStatus.OK)


class Test_ProcNode(unittest.TestCase):

    def test_build(self):
        p = ProcedureNode(WhiteHole())
        v1 = ValueNode(int)
        v2 = ValueNode(int)
        v3 = ValueNode(int)
        v4 = ValueNode(int)
        v5 = ValueNode(int)
        self.assertEqual(p.get_add_input_status(), ProcedureNode.AddInputStatus.NIL)
        self.assertEqual(p.get_add_output_status(), ProcedureNode.AddOutputStatus.NIL)
        self.assertEqual(p.get_inputs(), dict())
        self.assertEqual(p.get_outputs(), dict())
        p.add_input("a", v1)
        self.assertEqual(p.get_add_input_status(), ProcedureNode.AddInputStatus.OK)
        p.add_input("a", v1)
        self.assertEqual(p.get_add_input_status(), ProcedureNode.AddInputStatus.ALREADY_LINKED)
        p.add_input("a", v2)
        self.assertEqual(p.get_add_input_status(), ProcedureNode.AddInputStatus.DUPLICATE_NAME)
        p.add_input("b", v2)
        self.assertEqual(p.get_add_input_status(), ProcedureNode.AddInputStatus.OK)
        p.add_output("c", v1)
        self.assertEqual(p.get_add_output_status(), ProcedureNode.AddOutputStatus.ALREADY_LINKED)
        p.add_output("a", v3)
        self.assertEqual(p.get_add_output_status(), ProcedureNode.AddOutputStatus.DUPLICATE_NAME)
        p.add_output("c", v3)
        self.assertEqual(p.get_add_output_status(), ProcedureNode.AddOutputStatus.OK)
        p.add_input("d", v3)
        self.assertEqual(p.get_add_input_status(), ProcedureNode.AddInputStatus.ALREADY_LINKED)
        p.add_input("c", v4)
        self.assertEqual(p.get_add_input_status(), ProcedureNode.AddInputStatus.DUPLICATE_NAME)
        p.add_output("d", v4)
        self.assertEqual(p.get_add_output_status(), ProcedureNode.AddOutputStatus.OK)
        self.assertEqual(p.get_inputs(), {"a": v1, "b": v2})
        self.assertEqual(p.get_outputs(), {"c": v3, "d": v4})
        p.complete_build()
        p.add_input("e", v5)
        self.assertEqual(p.get_add_input_status(), ProcedureNode.AddInputStatus.BUILD_COMPLETE)
        p.add_output("e", v5)
        self.assertEqual(p.get_add_output_status(), ProcedureNode.AddOutputStatus.BUILD_COMPLETE)
        self.assertEqual(p.get_inputs(), {"a": v1, "b": v2})
        self.assertEqual(p.get_outputs(), {"c": v3, "d": v4})


    def test_invalidate(self):
        p = ProcedureNode(WhiteHole())
        v1 = ValueNode(int)
        v2 = ValueNode(int)
        p.add_output("a", v1)
        p.add_output("b", v2)
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.NIL)
        p.invalidate()
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.BUILD_INCOMPLETE)
        p.complete_build()
        v1.complete_build()
        v2.complete_build()
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.NIL)
        self.assertEqual(v2.get_invalidate_status(), ValueNode.InvalidateStatus.NIL)
        p.invalidate()
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.OK)
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v2.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        v1.put(1)
        v2.put(2)
        p.invalidate()
        self.assertEqual(p.get_invalidate_status(), ProcedureNode.InvalidateStatus.OK)
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v2.get_invalidate_status(), ValueNode.InvalidateStatus.OK)


    def test_run_empty(self):
        p = ProcedureNode(WhiteHole())
        v1 = ValueNode(int)
        v2 = ValueNode(int)
        v3 = ValueNode(int)
        v4 = ValueNode(int)
        p.add_input("a", v1)
        p.add_input("b", v2)
        p.add_output("c", v3)
        p.add_output("d", v4)
        v1.add_output(p)
        v2.add_output(p)
        v1.complete_build()
        v2.complete_build()
        v3.complete_build()
        v4.complete_build()
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.NIL)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.NIL)
        self.assertEqual(v2.get_validate_status(), ValueNode.ValidateStatus.NIL)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        self.assertEqual(v2.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        p.run()
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.BUILD_INCOMPLETE)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.NIL)
        self.assertEqual(v2.get_validate_status(), ValueNode.ValidateStatus.NIL)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        self.assertEqual(v2.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        p.complete_build()
        p.run()
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.INPUT_VALIDATION_FAILED)
        v1.put(1)
        v2.put(2)
        self.assertEqual(v3.get_put_status(), ValueNode.PutStatus.NIL)
        self.assertEqual(v4.get_put_status(), ValueNode.PutStatus.NIL)
        p.run()
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.FAIL)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(v2.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        self.assertEqual(v2.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        self.assertEqual(v3.get_put_status(), ValueNode.PutStatus.NIL)
        self.assertEqual(v4.get_put_status(), ValueNode.PutStatus.NIL)


    def test_run(self):
        p = ProcedureNode(BlackHole())
        v1 = ValueNode(int)
        v2 = ValueNode(int)
        v3 = ValueNode(int)
        v4 = ValueNode(int)
        p.add_input("a", v1)
        p.add_input("b", v2)
        p.add_output("c", v3)
        p.add_output("d", v4)
        v1.add_output(p)
        v2.add_output(p)
        v1.complete_build()
        v2.complete_build()
        v3.complete_build()
        v4.complete_build()
        p.complete_build()
        v1.put(1)
        v2.put(2)
        self.assertEqual(v3.get_put_status(), ValueNode.PutStatus.NIL)
        self.assertEqual(v4.get_put_status(), ValueNode.PutStatus.NIL)
        p.run()
        self.assertEqual(p.get_run_status(), ProcedureNode.RunStatus.OK)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(v2.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.OK)
        self.assertEqual(v2.get_used_by_status(), ValueNode.UsedByStatus.OK)
        self.assertEqual(v3.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v4.get_put_status(), ValueNode.PutStatus.OK)


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
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
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
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
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
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
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
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {"foo": int}, {}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {}, {"foo": int}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            ("a", int),
            ("b", int),
            ("a", str),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.DUPLICATE_NAME)
        self.assertEqual(s.get_init_message(), "Duplicate name: 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"left": "c"},
                {}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.NAME_NOT_FOUND)
        self.assertEqual(s.get_init_message(), "Input not found: 'left': 'c'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {},
                {"left": "c"}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.NAME_NOT_FOUND)
        self.assertEqual(s.get_init_message(), "Output not found: 'left': 'c'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"foo": "a", "boo": "a"},
                {}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.ALREADY_LINKED)
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"foo": "a"},
                {"boo": "a"}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.ALREADY_LINKED)
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {},
                {"foo": "a", "boo": "a"}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.ALREADY_LINKED)
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(), {}, {"foo": "a"}),
            (BlackHole(), {}, {"foo": "a"}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.TOO_MANY_INPUTS)
        self.assertEqual(s.get_init_message(), "Too many inputs: 'foo': 'a'")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {"foo": str}, {}),
        ])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.AUTO_VALUE_TYPE_MISMATCH)
        self.assertEqual(s.get_init_message(),
            "Auto value 'foo' type mismatch: <class 'str'> and <class 'int'>")


    def test_put(self):
        s = Simulator([("a", int), ("a", int)])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.DUPLICATE_NAME)
        self.assertEqual(s.get_put_status(), Simulator.PutStatus.NIL)
        s.put("a", 1)
        self.assertEqual(s.get_put_status(), Simulator.PutStatus.INTERNAL_ERROR)

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
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
        self.assertEqual(s.get_put_status(), Simulator.PutStatus.NIL)
        s.put("a", 1)
        self.assertEqual(s.get_put_status(), Simulator.PutStatus.OK)
        s.put("foo", 1)
        self.assertEqual(s.get_put_status(), Simulator.PutStatus.INVALID_NAME)
        s.put("c", 1)
        self.assertEqual(s.get_put_status(), Simulator.PutStatus.INVALID_NAME)


    def test_get(self):
        s = Simulator([("a", int), ("a", int)])
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.DUPLICATE_NAME)
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.NIL)
        s.get("a")
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.INTERNAL_ERROR)

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
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.NIL)
        s.get("foo")
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.INVALID_NAME)
        s.get("e")
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.INCOMPLETE_INPUT)
        s.put("a", 101)
        s.put("b", 7)
        self.assertEqual(s.get("e"), 4)
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.OK)
        self.assertEqual(s.get("c"), 14)
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.OK)


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
        self.assertEqual(s.get_init_status(), Simulator.InitStatus.OK)
        s.put("a", 101)
        s.put("b", 7)
        self.assertEqual(s.get("c"), 4)
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.OK)
        self.assertEqual(s.get("d"), 2)
        self.assertEqual(s.get_get_status(), Simulator.GetStatus.OK)


if __name__ == "__main__":
    unittest.main()
