import unittest

from impurity import ProgressManager

class Test_ProgressManager(unittest.TestCase):

    def test_flow(self):
        pm = ProgressManager(2, 3)
        self.assertEqual(pm.get_start_material_status, ProgressManager.StartMaterialStatus.NIL)
        self.assertEqual(pm.get_finish_material_status, ProgressManager.FinishMaterialStatus.NIL)
        self.assertEqual(pm.get_start_energy_status, ProgressManager.StartEnergyStatus.NIL)
        self.assertEqual(pm.get_finish_energy_status, ProgressManager.FinishEnergyStatus.NIL)
        pm.start_material(0)
        self.assertEqual(pm.get_start_material_status, ProgressManager.StartMaterialStatus.OK)
        pm.start_energy(0)
        self.assertEqual(pm.get_start_energy_status, ProgressManager.StartEnergyStatus.OK)


if __name__ == "__main__":
    unittest.main()

