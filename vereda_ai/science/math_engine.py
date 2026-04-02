from vereda_ai.math.symbolic_engine import SymbolicEngine
from vereda_ai.math.numeric_engine import NumericEngine


class MathEngine:
    """
    Motor matemático científico: combina simbólico (SymPy) e numérico (NumPy/SciPy).
    """

    def __init__(self) -> None:
        self.symbolic = SymbolicEngine()
        self.numeric = NumericEngine()

