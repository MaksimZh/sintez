import unittest

from nodes import ValueNode, ProcNode


class Test_ValueNode(unittest.TestCase):

    def test_build(self):
        v1 = ValueNode(int)
        p1 = ProcNode(object)
        p2 = ProcNode(object)
        p3 = ProcNode(object)
        p4 = ProcNode(object)
        self.assertEqual(v1.get_add_input_status(), ValueNode.AddInputStatus.NIL)
        self.assertEqual(v1.get_add_output_status(), ValueNode.AddOutputStatus.NIL)
        self.assertIsNone(v1.get_input())
        self.assertEqual(v1.get_outputs(), set())
        v1.add_output(p2)
        self.assertEqual(v1.get_add_output_status(), ValueNode.AddOutputStatus.OK)
        v1.add_output(p2)
        self.assertEqual(v1.get_add_output_status(), ValueNode.AddOutputStatus.ALREADY_LINKED)
        v1.add_input(p2)
        self.assertEqual(v1.get_add_input_status(), ValueNode.AddInputStatus.ALREADY_LINKED)
        v1.add_input(p1)
        self.assertEqual(v1.get_add_input_status(), ValueNode.AddInputStatus.OK)
        v1.add_input(p1)
        self.assertEqual(v1.get_add_input_status(), ValueNode.AddInputStatus.ALREADY_LINKED)
        v1.add_input(p3)
        self.assertEqual(v1.get_add_input_status(), ValueNode.AddInputStatus.TOO_MANY_INPUTS)
        v1.add_output(p1)
        self.assertEqual(v1.get_add_output_status(), ValueNode.AddOutputStatus.ALREADY_LINKED)
        v1.add_output(p3)
        self.assertEqual(v1.get_add_output_status(), ValueNode.AddOutputStatus.OK)
        v1.complete_build()
        v1.add_input(p4)
        self.assertEqual(v1.get_add_input_status(), ValueNode.AddInputStatus.BUILD_COMPLETE)
        v1.add_output(p4)
        self.assertEqual(v1.get_add_output_status(), ValueNode.AddOutputStatus.BUILD_COMPLETE)
        self.assertEqual(v1.get_input(), p1)
        self.assertEqual(v1.get_outputs(), {p2, p3})


    def test_get_state(self):
        v1 = ValueNode(int)
        self.assertEqual(v1.get_get_state_status(), ValueNode.GetStateStatus.NIL)
        v1.get_state()
        self.assertEqual(v1.get_get_state_status(), ValueNode.GetStateStatus.BUILD_INCOMPLETE)
        v1.complete_build()
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        self.assertEqual(v1.get_get_state_status(), ValueNode.GetStateStatus.OK)


    def test_put_last(self):
        v1 = ValueNode(int)
        self.assertEqual(v1.get_put_status(), ValueNode.PutStatus.NIL)
        v1.put(1)
        self.assertEqual(v1.get_put_status(), ValueNode.PutStatus.BUILD_INCOMPLETE)
        v1.complete_build()
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        v1.put(0.5)
        self.assertEqual(v1.get_put_status(), ValueNode.PutStatus.INCOMPATIBLE_TYPE)
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        v1.put(1)
        self.assertEqual(v1.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v1.get_state(), ValueNode.State.REGULAR)


    def test_put_mid(self):
        v1 = ValueNode(int)
        p1 = ProcNode(object)
        v1.add_output(p1)
        self.assertEqual(v1.get_put_status(), ValueNode.PutStatus.NIL)
        v1.put(1)
        self.assertEqual(v1.get_put_status(), ValueNode.PutStatus.BUILD_INCOMPLETE)
        v1.complete_build()
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p1.get_input_state_change_status(), ProcNode.InputStateChangeStatus.NIL)
        v1.put(0.5)
        self.assertEqual(v1.get_put_status(), ValueNode.PutStatus.INCOMPATIBLE_TYPE)
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p1.get_input_state_change_status(), ProcNode.InputStateChangeStatus.NIL)
        v1.put(1)
        self.assertEqual(v1.get_put_status(), ValueNode.PutStatus.OK)
        self.assertEqual(v1.get_state(), ValueNode.State.NEW)
        self.assertEqual(p1.get_input_state_change_status(), ProcNode.InputStateChangeStatus.OK)


    def test_invalidate(self):
        v1 = ValueNode(int)
        p1 = ProcNode(object)
        v1.add_output(p1)
        p1.complete_build()
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.NIL)
        v1.invalidate()
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.BUILD_INCOMPLETE)
        v1.complete_build()
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p1.get_input_state_change_status(), ProcNode.InputStateChangeStatus.NIL)
        v1.invalidate()
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p1.get_input_state_change_status(), ProcNode.InputStateChangeStatus.NIL)
        v1.put(1)
        self.assertEqual(v1.get_state(), ValueNode.State.NEW)
        v1.invalidate()
        self.assertEqual(v1.get_invalidate_status(), ValueNode.InvalidateStatus.OK)
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        self.assertEqual(p1.get_input_state_change_status(), ProcNode.InputStateChangeStatus.OK)

    
    def test_used(self):
        v1 = ValueNode(int)
        p1 = ProcNode(object)
        p2 = ProcNode(object)
        p3 = ProcNode(object)
        v1.add_output(p1)
        v1.add_output(p2)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.NIL)
        v1.used_by(p1)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.BUILD_INCOMPLETE)
        v1.complete_build()
        self.assertEqual(v1.get_state(), ValueNode.State.INVALID)
        v1.used_by(p1)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.INVALID_VALUE)
        v1.put(1)
        self.assertEqual(v1.get_state(), ValueNode.State.NEW)
        v1.used_by(p1)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.OK)
        self.assertEqual(v1.get_state(), ValueNode.State.NEW)
        v1.used_by(p3)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.NOT_OUTPUT)
        self.assertEqual(v1.get_state(), ValueNode.State.NEW)
        v1.used_by(p2)
        self.assertEqual(v1.get_used_by_status(), ValueNode.UsedByStatus.OK)
        self.assertEqual(v1.get_state(), ValueNode.State.REGULAR)


    def test_validate_first(self):
        v1 = ValueNode(int)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.NIL)
        v1.validate()
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.BUILD_INCOMPLETE)
        v1.complete_build()
        v1.validate()
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.NO_VALUE_SOURCE)
        v1.put(1)
        v1.validate()
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.OK)


    def test_validate_mid(self):
        v1 = ValueNode(int)
        p1 = ProcNode(int)
        v1.add_input(p1)
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.NIL)
        v1.validate()
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.BUILD_INCOMPLETE)
        v1.complete_build()
        self.assertEqual(p1.get_run_status(), ProcNode.RunStatus.NIL)
        v1.validate()
        self.assertEqual(v1.get_validate_status(), ValueNode.ValidateStatus.OK)
        self.assertEqual(p1.get_run_status(), ProcNode.RunStatus.OK)


    def test_get(self):
        v1 = ValueNode(int)
        self.assertEqual(v1.get_get_status(), ValueNode.GetStatus.NIL)
        v1.get()
        self.assertEqual(v1.get_get_status(), ValueNode.GetStatus.BUILD_INCOMPLETE)
        v1.complete_build()
        v1.get()
        self.assertEqual(v1.get_get_status(), ValueNode.GetStatus.INVALID_VALUE)
        v1.put(1)
        self.assertEqual(v1.get(), 1)
        self.assertEqual(v1.get_get_status(), ValueNode.GetStatus.OK)




if __name__ == "__main__":
    unittest.main()
