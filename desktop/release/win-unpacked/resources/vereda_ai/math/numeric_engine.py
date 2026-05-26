import numpy as np
import scipy.linalg as la


class NumericEngine:
    """
    Álgebra linear numérica, autovalores, sistemas, etc.
    """

    def solve_linear_system(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        return la.solve(A, b)

    def eigen(self, A: np.ndarray):
        return la.eig(A)

