import unittest
from typing import Type

from nodes import ValueNode, ProcNode, \
    ProcInput, ProcOutput, ProcNodeIO, ProcNodeInput, ProcNodeOutput


class FailProc:

    def __init__(self, input: ProcInput, output: ProcOutput) -> None:
        pass

    def run(self) -> None:
        pass


class SuccessProc:

    __input: ProcInput
    __output: ProcOutput

    def __init__(self, input: ProcInput, output: ProcOutput) -> None:
        self.__input = input
        self.__output = output

    def run(self) -> None:
        for name in self.__input.get_nodes().keys():
            self.__input.get(name)
        for name in self.__output.get_nodes().keys():
            self.__output.put(name, self.__output.get_type(name)())


class Test_ValueNode(unittest.TestCase):

    def test_build(self):
        v = ValueNode(int)
        p1 = ProcNode(FailProc)
        p2 = ProcNode(FailProc)
        p3 = ProcNode(FailProc)
        p4 = ProcNode(FailProc)
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
        v = ValueNode(int)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        v.put(0.5)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.INCOMPATIBLE_TYPE)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.REGULAR)


    def test_put_mid(self):
        v = ValueNode(int)
        p = ProcNode(FailProc)
        v.add_output(p)
        p.complete_build()
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.NIL)
        v.put(0.5)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.INCOMPATIBLE_TYPE)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.OK)


    def test_invalidate(self):
        v = ValueNode(int)
        p = ProcNode(FailProc)
        v.add_output(p)
        p.complete_build()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.NIL)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.NIL)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.OK)

    
    def test_used(self):
        v = ValueNode(int)
        p1 = ProcNode(FailProc)
        p2 = ProcNode(FailProc)
        p3 = ProcNode(FailProc)
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
        p = ProcNode(FailProc)
        v.add_input(p)
        p.add_output("a", v)
        p.complete_build()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.INPUT_FAILED)
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.INCOMPLETE_OUTPUT)

    
    def test_validate_mid_success(self):
        v = ValueNode(int)
        p = ProcNode(SuccessProc)
        v.add_input(p)
        p.add_output("a", v)
        p.complete_build()
        v.complete_build()
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.OK)

    
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


class Test_ProcNodeIO(unittest.TestCase):

    T: Type[ProcNodeIO]

    def test_build(self):
        o = self.T()
        v1 = ValueNode(int)
        v2 = ValueNode(str)
        v3 = ValueNode(float)
        self.assertEqual(o.get_add_status(), self.T.AddStatus.NIL)
        o.add("a", v1)
        self.assertEqual(o.get_add_status(), self.T.AddStatus.OK)
        o.add("b", v1)
        self.assertEqual(o.get_add_status(), self.T.AddStatus.DUPLICATE_NODE)
        o.add("a", v2)
        self.assertEqual(o.get_add_status(), self.T.AddStatus.DUPLICATE_NAME)
        o.add("b", v2)
        self.assertEqual(o.get_add_status(), self.T.AddStatus.OK)
        self.assertEqual(o.get_nodes(), {"a": v1, "b": v2})
        o.complete_build()
        o.add("c", v3)
        self.assertEqual(o.get_add_status(), self.T.AddStatus.BUILD_COMPLETE)
        self.assertEqual(o.get_nodes(), {"a": v1, "b": v2})

    
    def test_has(self):
        o = self.T()
        v1 = ValueNode(int)
        v2 = ValueNode(str)
        v3 = ValueNode(float)
        o.add("a", v1)
        o.add("b", v2)
        self.assertTrue(o.has_name("a"))
        self.assertTrue(o.has_name("b"))
        self.assertFalse(o.has_name("c"))
        self.assertTrue(o.has_node(v1))
        self.assertTrue(o.has_node(v2))
        self.assertFalse(o.has_node(v3))

    
    def test_get_type(self):
        o = self.T()
        v1 = ValueNode(int)
        v2 = ValueNode(str)
        o.add("a", v1)
        o.add("b", v2)
        self.assertEqual(o.get_get_type_status(), self.T.GetTypeStatus.NIL)
        self.assertIs(o.get_type("a"), int)
        self.assertEqual(o.get_get_type_status(), self.T.GetTypeStatus.OK)
        self.assertIs(o.get_type("b"), str)
        self.assertEqual(o.get_get_type_status(), self.T.GetTypeStatus.OK)
        o.get_type("c")
        self.assertEqual(o.get_get_type_status(), self.T.GetTypeStatus.NOT_FOUND)


class Test_ProcNodeInput(Test_ProcNodeIO):

    def __init__(self, methodName: str = ...) -> None:
        self.T = ProcNodeInput
        super().__init__(methodName)


    def test_get(self):
        o = ProcNodeInput()
        v1 = ValueNode(int)
        v2 = ValueNode(str)
        v1.complete_build()
        v2.complete_build()
        o.add("a", v1)
        o.add("b", v2)
        v1.put(1)
        v2.put("foo")
        self.assertEqual(o.get_get_status(), ProcNodeInput.GetStatus.NIL)
        o.get("a")
        self.assertEqual(o.get_get_status(), ProcNodeInput.GetStatus.BUILD_INCOMPLETE)
        o.complete_build()
        self.assertEqual(o.get("a"), 1)
        self.assertEqual(o.get_get_status(), ProcNodeInput.GetStatus.OK)
        self.assertEqual(o.get("b"), "foo")
        self.assertEqual(o.get_get_status(), ProcNodeInput.GetStatus.OK)
        o.get("c")
        self.assertEqual(o.get_get_status(), ProcNodeInput.GetStatus.NOT_FOUND)


class Test_ProcNodeOutput(Test_ProcNodeIO):

    def __init__(self, methodName: str = ...) -> None:
        self.T = ProcNodeOutput
        super().__init__(methodName)

    def test_put(self):
        o = ProcNodeOutput()
        v = ValueNode(int)
        v.complete_build()
        o.add("a", v)
        self.assertEqual(o.get_put_status(), ProcNodeOutput.PutStatus.NIL)
        o.put("a", 1)
        self.assertEqual(o.get_put_status(), ProcNodeOutput.PutStatus.BUILD_INCOMPLETE)
        o.complete_build()
        o.put("b", 1)
        self.assertEqual(o.get_put_status(), ProcNodeOutput.PutStatus.NOT_FOUND)
        o.put("a", "foo")
        self.assertEqual(o.get_put_status(), ProcNodeOutput.PutStatus.INCOMPATIBLE_TYPE)
        o.put("a", 1)
        self.assertEqual(o.get_put_status(), ProcNodeOutput.PutStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.REGULAR)
        self.assertEqual(v.get(), 1)

    
    def test_output_check(self):
        o = ProcNodeOutput()
        v1 = ValueNode(int)
        v2 = ValueNode(int)
        v1.complete_build()
        v2.complete_build()
        o.add("a", v1)
        o.add("b", v2)
        self.assertEqual(o.get_reset_output_check_status(),
            ProcNodeOutput.ResetOutputCheckStatus.NIL)
        self.assertEqual(o.get_is_output_complete_status(),
            ProcNodeOutput.IsOutputCompleteStatus.NIL)
        o.reset_output_check()
        self.assertEqual(o.get_reset_output_check_status(),
            ProcNodeOutput.ResetOutputCheckStatus.BUILD_INCOMPLETE)
        o.is_output_complete()
        self.assertEqual(o.get_is_output_complete_status(),
            ProcNodeOutput.IsOutputCompleteStatus.BUILD_INCOMPLETE)
        o.complete_build()
        o.reset_output_check()
        self.assertEqual(o.get_reset_output_check_status(),
            ProcNodeOutput.ResetOutputCheckStatus.OK)
        self.assertFalse(o.is_output_complete())
        self.assertEqual(o.get_is_output_complete_status(),
            ProcNodeOutput.IsOutputCompleteStatus.OK)
        o.put("a", 1)
        self.assertFalse(o.is_output_complete())
        self.assertEqual(o.get_is_output_complete_status(),
            ProcNodeOutput.IsOutputCompleteStatus.OK)
        o.put("b", 2)
        self.assertTrue(o.is_output_complete())
        self.assertEqual(o.get_is_output_complete_status(),
            ProcNodeOutput.IsOutputCompleteStatus.OK)


class Test_ProcNode(unittest.TestCase):

    def test_build(self):
        p = ProcNode(FailProc)
        v1 = ValueNode(int)
        v2 = ValueNode(int)
        v3 = ValueNode(int)
        v4 = ValueNode(int)
        v5 = ValueNode(int)
        self.assertEqual(p.get_add_input_status(), ProcNode.AddInputStatus.NIL)
        self.assertEqual(p.get_add_output_status(), ProcNode.AddOutputStatus.NIL)
        self.assertEqual(p.get_inputs(), dict())
        self.assertEqual(p.get_outputs(), dict())
        p.add_input("a", v1)
        self.assertEqual(p.get_add_input_status(), ProcNode.AddInputStatus.OK)
        p.add_input("a", v1)
        self.assertEqual(p.get_add_input_status(), ProcNode.AddInputStatus.ALREADY_LINKED)
        p.add_input("a", v2)
        self.assertEqual(p.get_add_input_status(), ProcNode.AddInputStatus.DUPLICATE_NAME)
        p.add_input("b", v2)
        self.assertEqual(p.get_add_input_status(), ProcNode.AddInputStatus.OK)
        p.add_output("c", v1)
        self.assertEqual(p.get_add_output_status(), ProcNode.AddOutputStatus.ALREADY_LINKED)
        p.add_output("a", v3)
        self.assertEqual(p.get_add_output_status(), ProcNode.AddOutputStatus.DUPLICATE_NAME)
        p.add_output("c", v3)
        self.assertEqual(p.get_add_output_status(), ProcNode.AddOutputStatus.OK)
        p.add_input("d", v3)
        self.assertEqual(p.get_add_input_status(), ProcNode.AddInputStatus.ALREADY_LINKED)
        p.add_input("c", v4)
        self.assertEqual(p.get_add_input_status(), ProcNode.AddInputStatus.DUPLICATE_NAME)
        p.add_output("d", v4)
        self.assertEqual(p.get_add_output_status(), ProcNode.AddOutputStatus.OK)
        self.assertEqual(p.get_inputs(), {"a": v1, "b": v2})
        self.assertEqual(p.get_outputs(), {"c": v3, "d": v4})
        p.complete_build()
        p.add_input("e", v5)
        self.assertEqual(p.get_add_input_status(), ProcNode.AddInputStatus.BUILD_COMPLETE)
        p.add_output("e", v5)
        self.assertEqual(p.get_add_output_status(), ProcNode.AddOutputStatus.BUILD_COMPLETE)
        self.assertEqual(p.get_inputs(), {"a": v1, "b": v2})
        self.assertEqual(p.get_outputs(), {"c": v3, "d": v4})

    
    def test_invalidate(self):
        p = ProcNode(FailProc)
        v1 = ValueNode(int)
        v2 = ValueNode(int)
        p.add_output("a", v1)
        p.add_output("b", v2)
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.NIL)
        p.invalidate()
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.BUILD_INCOMPLETE)
        p.complete_build()
        v1.complete_build()
        v2.complete_build()
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.NIL)
        self.assertEqual(v2.get_invalidate_status(), ValueNode.InvalidateStatus.NIL)
        p.invalidate()
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.OK)
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v2.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        v1.put(1)
        v2.put(2)
        p.invalidate()
        self.assertEqual(p.get_invalidate_status(), ProcNode.InvalidateStatus.OK)
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v2.get_invalidate_status(), ValueNode.InvalidateStatus.OK)

    
    def test_run_empty(self):
        p = ProcNode(FailProc)
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
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.NIL)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.NIL)
        self.assertEqual(v2.get_validate_status(), ValueNode.ValidateStatus.NIL)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        self.assertEqual(v2.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        p.run()
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.BUILD_INCOMPLETE)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.NIL)
        self.assertEqual(v2.get_validate_status(), ValueNode.ValidateStatus.NIL)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        self.assertEqual(v2.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        p.complete_build()
        v1.put(1)
        v2.put(2)
        self.assertEqual(v3.get_put_status(), ValueNode.PutStatus.NIL)
        self.assertEqual(v4.get_put_status(), ValueNode.PutStatus.NIL)
        p.run()
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.INCOMPLETE_OUTPUT)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(v2.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        self.assertEqual(v2.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        self.assertEqual(v3.get_put_status(), ValueNode.PutStatus.NIL)
        self.assertEqual(v4.get_put_status(), ValueNode.PutStatus.NIL)

    
    def test_run(self):
        p = ProcNode(SuccessProc)
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
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.OK)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(v2.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.OK)
        self.assertEqual(v2.get_used_by_status(), ValueNode.UsedByStatus.OK)
        self.assertEqual(v3.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v4.get_put_status(), ValueNode.PutStatus.OK)


if __name__ == "__main__":
    del Test_ProcNodeIO
    unittest.main()
