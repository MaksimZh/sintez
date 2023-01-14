from enum import Enum, auto
from typing import Generator, Iterable

class Material:

    # CONSTRUCTOR
    def __init__(self, x: float) -> None:
        pass


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

    # CONSTRUCTOR
    # POST: creates collection with items passed
    def __init__(self, items: Iterable[float]) -> None:
        pass
    
    
    # QUERIES

    # get generator listing all items
    def items(self) -> Generator[float, None, None]:
        return
        yield


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


import numpy as np

def update_spectrum(spectrum: Spectrum, model: Model, energies: EnergyCollection):
    pass

xs = np.linspace(0, 0.3, 31)
energies = EnergyCollection([])
spectra = SpectraCollection("")
for x in xs:
    material = Material(x)
    model = Model(material)
    spectrum = spectra.get(model) if spectra.has(model) else Spectrum()
    update_spectrum(spectrum, model, energies)
    spectra.put(model, spectrum)
