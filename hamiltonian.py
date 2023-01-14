import numpy as np
import nptyping as npt

class ScalarHamiltonianMesh:
    def __init__(self) -> None:
        pass

    def as_array(self) -> npt.NDArray[npt.Shape["*, *, *"], npt.Complex]:
        return np.array([[[0]]], dtype=complex)
