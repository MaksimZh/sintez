from dataclasses import dataclass
from nodes import Simulator, Procedure
from typing import Any

@dataclass
class AngularParams:
    pass

@dataclass
class ImpurityParams:
    pass

@dataclass
class MeshParams:
    pass

class Hamiltonian:
    pass


class HamiltonianCalculator(Procedure):

    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.OK
    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.OK
        return Hamiltonian()


class SchrodingerEquationSolver(Procedure):

    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.OK
    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.OK
        return 0


simulator = Simulator([
    ("x", float),
    ("temperature", float),
    ("angular_params", AngularParams),
    ("impurity_params", ImpurityParams),
    (HamiltonianCalculator(),
        {
            "x": "x",
            "temperature": "temperature",
            "angular_params": "angular_params",
            "impurity_params": "impurity_params",
        },
        {
            "hamiltonian": "hamiltonian",
        }),
    ("hamiltonian", Hamiltonian),
    ("energy", float),
    ("radial_mesh", MeshParams),
    (SchrodingerEquationSolver(),
        {
            "hamiltonian": "hamiltonian",
            "energy": "energy",
            "radial_mesh": "radial_mesh",
        },
        {
            "localization_rate": "localization_rate",
        }),
    ("localization_rate", float),
])
assert(simulator.get_init_status() == Simulator.InitStatus.OK)
simulator.put("x", 0)
simulator.put("temperature", 0)
simulator.put("angular_params", AngularParams())
simulator.put("impurity_params", ImpurityParams())
simulator.put("energy", 1)
simulator.put("radial_mesh", MeshParams())
print(simulator.get("localization_rate"))
assert(simulator.get_get_status() == Simulator.GetStatus.OK)
