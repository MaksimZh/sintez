from dataclasses import dataclass
from nodes import Simulator, ProcInput, ProcOutput

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


class HamiltonianCalculator:

    def __init__(self, input: ProcInput, output: ProcOutput) -> None:
        pass

    def run(self) -> None:
        pass


class SchrodingerEquationSolver:

    def __init__(self, input: ProcInput, output: ProcOutput) -> None:
        pass

    def run(self) -> None:
        pass


class LocalizationRateCalculator:

    __input: ProcInput
    __output: ProcOutput
    __simulator: Simulator

    
    def __init__(self, input: ProcInput, output: ProcOutput) -> None:
        self.__input = input
        self.__output = output
        self.__simulator = Simulator([
            ("x", float),
            ("temperature", float),
            ("angular_params", AngularParams),
            ("impurity_params", ImpurityParams),
            (HamiltonianCalculator,
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
            (SchrodingerEquationSolver,
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
        assert(self.__simulator.get_init_status() == Simulator.InitStatus.OK)

    def __get(self, name: str) -> None:
        is_new = self.__input.is_new(name)
        assert(self.__input.get_is_new_status() == ProcInput.IsNewStatus.OK)
        if not is_new:
            return
        self.__simulator.put(name, self.__input.get(name))
        assert(self.__input.get_get_status() == ProcInput.GetStatus.OK)
        assert(self.__simulator.get_put_status() == Simulator.PutStatus.OK)

    def __put(self, name: str) -> None:
        is_new = self.__input.is_new(name)
        assert(self.__input.get_is_new_status() == ProcInput.IsNewStatus.OK)
        if not is_new:
            return
        self.__simulator.put(name, self.__input.get(name))
        assert(self.__input.get_get_status() == ProcInput.GetStatus.OK)
        assert(self.__simulator.get_put_status() == Simulator.PutStatus.OK)
    
    def run(self) -> None:
        self.__get("x")
        self.__get("temperature")
        self.__get("angular_params")
        self.__get("impurity_params")
        self.__get("energy")
        self.__get("radial_mesh")
        self.__put("localization_rate")


simulator = Simulator([
    ("x", float),
    ("temperature", float),
    ("angular_params", AngularParams),
    ("impurity_params", ImpurityParams),
    ("energy", float),
    ("radial_mesh", MeshParams),
    (LocalizationRateCalculator,
        {
            "x": "x",
            "temperature": "temperature",
            "angular_params": "angular_params",
            "impurity_params": "impurity_params",
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
