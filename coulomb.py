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
    (HamiltonianCalculator(),
        {
            "x": float,
            "temperature": float,
            "angular_params": AngularParams,
            "impurity_params": ImpurityParams,
        },
        {
            "hamiltonian": Hamiltonian,
        }),
    (SchrodingerEquationSolver(),
        {
            "hamiltonian": Hamiltonian,
            "energy": float,
            "radial_mesh": MeshParams,
        },
        {
            "localization_rate": float,
        }),
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
