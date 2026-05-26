from vereda_ai.math.symbolic_engine import SymbolicEngine
from vereda_ai.math.physics_engine import PhysicsEngine
from vereda_ai.math.engineering_engine import EngineeringEngine


class MathSolver:
    """
    Fachada para problemas de matemática, física e engenharia.
    """

    def __init__(self) -> None:
        self.symbolic = SymbolicEngine()
        self.physics = PhysicsEngine()
        self.engineering = EngineeringEngine()

