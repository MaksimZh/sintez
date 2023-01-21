from dataclasses import dataclass
from nodes import Simulator, Procedure
from typing import cast, Any

import numpy as np

@dataclass
class AngularParams:
    j: float
    l: int

@dataclass
class ImpurityParams:
    z: float
    z1: float
    l1: float

@dataclass
class MeshParams:
    r_seg: float
    r_max: float
    n_seg: int
    n_sub_seg: int

class Material:
    pass

class BulkHamiltonian:
    pass

class SphericalBulkHamiltonian:
    pass

class ImpuritySphericalHamiltonian:
    pass

class MaterialBuilder(Procedure):

    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.OK
    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.OK
        return 0

class BulkHamiltonianCalculator(Procedure):

    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.OK
    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.OK
        return 0

class SphericalHamiltonianCalculator(Procedure):

    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.OK
    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.OK
        return 0

class ImpurityHamiltonianCalculator(Procedure):

    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.OK
    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.OK
        return 0

class SchrodingerEquationSolver(Procedure):

    def put(self, name: str, value: Any) -> None:
        self._put_status = self.PutStatus.OK
    
    def get(self, name: str) -> Any:
        self._get_status = self.GetStatus.OK
        return 0

temperature_kelvin = 0
angular_params = AngularParams(3/2, 1)
impurity_params = ImpurityParams(-1, 0, 0)
radial_mesh = MeshParams(100, 100, 100, 10)

hamiltonian_calculator = Simulator([
    (MaterialBuilder(),
        {"x": float, "temperature": float},
        {"material": Material}),
    (BulkHamiltonianCalculator(),
        {"material": Material},
        {"hamiltonian": "bulk_hamiltonian"}),
    ("bulk_hamiltonian", BulkHamiltonian),
    (SphericalHamiltonianCalculator(),
        {
            "bulk_hamiltonian": "bulk_hamiltonian",
            "angular_params": AngularParams,
        },
        {"spherical_hamiltonian": "spherical_hamiltonian"}),
    ("spherical_hamiltonian", SphericalBulkHamiltonian),
    (ImpurityHamiltonianCalculator(),
        {
            "bulk_hamiltonian": "spherical_hamiltonian",
            "impurity_params": ImpurityParams,
        },
        {"impurity_hamiltonian": "hamiltonian"}),
    ("hamiltonian", ImpuritySphericalHamiltonian)
])

simulator = Simulator([
    (hamiltonian_calculator,
        {
            "x": float,
            "temperature": float,
            "angular_params": AngularParams,
            "impurity_params": ImpurityParams,
        },
        {
            "hamiltonian": ImpuritySphericalHamiltonian,
        }),
    (SchrodingerEquationSolver(),
        {
            "hamiltonian": ImpuritySphericalHamiltonian,
            "energy": float,
            "radial_mesh": MeshParams,
        },
        {
            "localization_rate": float,
        }),
])
assert simulator.get_init_status() == Simulator.InitStatus.OK
simulator.put("temperature", temperature_kelvin)
simulator.put("angular_params", angular_params)
simulator.put("impurity_params", impurity_params)
simulator.put("radial_mesh", radial_mesh)

simulator.put("x", 0)
simulator.put("energy", 1)
print(simulator.get("localization_rate"))
assert simulator.get_get_status() == Simulator.GetStatus.OK

def calc(energies):
    r = solver.create_radial_mesh(meshParams)
    model = Hamiltonian(params)
    detQ = []
    for energy in energies:
        print(f"energy = {energy:6.2f}")
        detQ.append(np.linalg.det(solver.calc_localization_matrix(model, energy, meshParams)))
    detQ = np.array(detQ)
    return r, detQ, model.eg


for x in np.linspace(0, X_MAX, int(X_MAX / X_STEP + 0.1) + 1):
    with h5py.File(source_dir + fileName, "a") as f:
        key = paramKey(x)
        if key in f:
            print("exists", key)
            # calculation will be made only for missing energy values
            g = cast(h5py.Group, f[key])
            oldEnergies = cast(h5py.Dataset, g["energies"])
            calcEnergies = energies_meV[np.logical_not(
                np.isclose(energies_meV[:, np.newaxis], oldEnergies).any(1))]
            r, detQ, eg = calc(params, calcEnergies, meshParams)
            newEnergies = np.concatenate((oldEnergies, calcEnergies))
            s = np.argsort(newEnergies)
            newEnergies = newEnergies[s]
            newDetQ = np.concatenate((g["detQ"], detQ))[s]
            del g["energies"]
            del g["detQ"]
            g.create_dataset("energies", data=newEnergies)
            g.create_dataset("detQ", data=newDetQ)
            print()
        else:
            print("calculating", key)
            r, detQ, eg = calc(params, energies_meV, meshParams)
            print("creating", key)
            g = f.create_group(key)
            g.attrs["x"] = params.x
            g.attrs["z"] = params.z
            g.attrs["z1"] = params.z1
            g.attrs["l1"] = params.l1
            g.attrs["j"] = params.j
            g.attrs["l"] = params.l
            g.attrs["eg"] = eg
            g.create_dataset("energies", data=energies_meV)
            g.create_dataset("detQ", data=detQ)
            print()