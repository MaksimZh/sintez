from enum import Enum, auto
from typing import Generator, Iterable

class Material:

    __x: float

    # CONSTRUCTOR
    def __init__(self, x: float) -> None:
        self.__x = x

    def get_x(self) -> float:
        return self.__x


class Model:

    # CONSTRUCTOR
    def __init__(self, material: Material) -> None:
        pass


class Spectrum:

    # CONSTRUCTOR
    # create empty spectrum
    def __init__(self) -> None:
        self.__get_status = self.GetStatus.NIL

    
    # QUERIES

    # check if spectrum has entry with specified energy
    def has(self, energy: float) -> bool:
        return False

    # get item with specified energy
    # PRE: spectrum contains specified energy
    def get(self, energy: float) -> float:
        return 0

    class GetStatus(Enum):
        NIL = auto(),
        OK = auto(),
        NOT_FOUND = auto(),

    __get_status: GetStatus

    def get_get_status(self) -> GetStatus:
        return self.__get_status


    # get generator listing all items
    def items(self) -> Generator[tuple[float, float], None, None]:
        return
        yield


class EnergyCollection:

    __data: list[float]

    # CONSTRUCTOR
    # POST: creates collection with items passed
    def __init__(self, items: Iterable[float]) -> None:
        self.__data = list(items)
    
    
    # QUERIES

    # get collection size
    def get_size(self) -> int:
        return len(self.__data)

    # get generator listing all items
    def get_items(self) -> Generator[float, None, None]:
        for v in self.__data:
            yield v


class SpectraCollection:
    
    # CONSTRUCTOR
    # POST: creates spectra collection wrapping specified HDF5 file
    def __init__(self, file_name: str) -> None:
        self.__put_status = self.PutStatus.NIL
        self.__get_status = self.GetStatus.NIL


    # COMANDS

    # add new spectrum or update existing one
    def put(self, model: Model, spectrum: Spectrum) -> None:
        pass

    class PutStatus(Enum):
        NIL = auto(),
        OK = auto(),
        NEW = auto(),
        UPDATED = auto(),

    __put_status: PutStatus

    def get_put_status(self) -> PutStatus:
        return self.__put_status


    # QUERIES

    # check if the spectrum for model is in the collection
    def has(self, model: Model) -> bool:
        return False
    
    # get spectrum by key
    # PRE: spectrum for model is in the collection
    def get(self, model: Model) -> Spectrum:
        return Spectrum()

    class GetStatus(Enum):
        NIL = auto(),
        OK = auto(),
        NOT_FOUND = auto(),

    __get_status: GetStatus

    def get_get_status(self) -> GetStatus:
        return self.__get_status


class Hamiltonian:
    pass


class ProgressManager:

    __num_energies: int
    __energy_index: int

    # CONSTRUCTOR
    def __init__(self, num_materials: int, num_energies: int) -> None:
        self.__num_energies = num_energies
        self.__start_material_status = self.StartMaterialStatus.NIL
        self.__start_energy_status = self.StartEnergyStatus.NIL
        self.__finish_status = self.FinishStatus.NIL
    

    # COMMANDS

    # start progress of new material calculation
    # PRE: material number not exhausted
    # PRE: energy number exhausted
    def start_material(self, material: Material) -> None:
        print("material: ", material.get_x())
        self.__energy_index = 0
        self.__start_material_status = self.StartMaterialStatus.OK

    class StartMaterialStatus(Enum):
        NIL = auto(),
        OK = auto(),
        EXHAUSTED = auto(),
        MISSING_ENERGIES = auto(),

    __start_material_status: StartMaterialStatus
    
    def get_start_material_status(self) -> StartMaterialStatus:
        return self.__start_material_status


    # start progress of new energy calculation
    # PRE: material progress started
    # PRE: energy or material number not exhausted
    def start_energy(self, energy: float) -> None:
        print("    energy =", energy)
        self.__energy_index += 1

    class StartEnergyStatus(Enum):
        NIL = auto(),
        OK = auto(),
        EXHAUSTED = auto(),

    __start_energy_status: StartEnergyStatus
    
    def get_start_energy_status(self) -> StartEnergyStatus:
        return self.__start_energy_status


    # end all progress
    # PRE: any progress started
    def finish(self) -> None:
        pass

    class FinishStatus(Enum):
        NIL = auto(),
        OK = auto(),
        NOT_STARTED = auto(),

    __finish_status: FinishStatus
    
    def get_finish_status(self) -> FinishStatus:
        return self.__finish_status


import numpy as np

def update_spectrum(spectrum: Spectrum, model: Model, energies: EnergyCollection, progress: ProgressManager):
    for energy in energies.get_items():
        progress.start_energy(energy)

xs = np.linspace(0, 0.3, 31)
energies = EnergyCollection(range(10))
spectra = SpectraCollection("")
progress = ProgressManager(len(xs), energies.get_size())
for x in xs:
    material = Material(x)
    progress.start_material(material)
    model = Model(material)
    spectrum = spectra.get(model) if spectra.has(model) else Spectrum()
    update_spectrum(spectrum, model, energies, progress)
    spectra.put(model, spectrum)
progress.finish()
