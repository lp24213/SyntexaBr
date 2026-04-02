from dataclasses import dataclass


@dataclass
class BeamLoadResult:
    max_moment: float
    max_deflection: float


class EngineeringEngine:
    """
    Cálculos de engenharia mecânica / estrutural simplificados.
    """

    def cantilever_beam_point_load(
        self, length: float, load: float, e_modulus: float, inertia: float
    ) -> BeamLoadResult:
        """
        Viga em balanço com carga concentrada na ponta.
        M_max = P*L
        δ_max = P*L^3 / (3*E*I)
        """
        max_moment = load * length
        max_deflection = load * length**3 / (3 * e_modulus * inertia)
        return BeamLoadResult(max_moment=max_moment, max_deflection=max_deflection)

