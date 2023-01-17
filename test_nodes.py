import unittest

from nodes import ValueNode, ProcNode


class Test_ValueNode(unittest.TestCase):

    def test_build(self):
        v = ValueNode(int)
        p1 = ProcNode(object)
        p2 = ProcNode(object)
        p3 = ProcNode(object)
        p4 = ProcNode(object)
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
        p = ProcNode(object)
        v.add_output(p)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_input_state_change_status(), ProcNode.InputStateChangeStatus.NIL)
        v.put(0.5)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.INCOMPATIBLE_TYPE)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_input_state_change_status(), ProcNode.InputStateChangeStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        self.assertEqual(p.get_input_state_change_status(), ProcNode.InputStateChangeStatus.OK)


    def test_invalidate(self):
        v = ValueNode(int)
        p = ProcNode(object)
        v.add_output(p)
        p.complete_build()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.NIL)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_input_state_change_status(), ProcNode.InputStateChangeStatus.NIL)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_input_state_change_status(), ProcNode.InputStateChangeStatus.NIL)
        v.put(1)
        self.assertEqual(v.get_state(), ValueNode.State.NEW)
        v.invalidate()
        self.assertEqual(v.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p.get_input_state_change_status(), ProcNode.InputStateChangeStatus.OK)

    
    def test_used(self):
        v = ValueNode(int)
        p1 = ProcNode(object)
        p2 = ProcNode(object)
        p3 = ProcNode(object)
        v.add_output(p1)
        v.add_output(p2)
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


    def test_validate_mid(self):
        v = ValueNode(int)
        p = ProcNode(int)
        v.add_input(p)
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.BUILD_INCOMPLETE)
        v.complete_build()
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.NIL)
        v.validate()
        self.assertEqual(v.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(p.get_run_status(), ProcNode.RunStatus.OK)


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



if __name__ == "__main__":
    unittest.main()
