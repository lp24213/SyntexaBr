class PhysicsEngine:
    """
    Cálculos físicos básicos para forças, energia, transferência de calor, etc.
    """

    def newton_second_law(self, mass: float, acceleration: float) -> float:
        return mass * acceleration

    def kinetic_energy(self, mass: float, velocity: float) -> float:
        return 0.5 * mass * velocity**2

    def heat_flux_1d(self, k: float, area: float, dT: float, dx: float) -> float:
        # Lei de Fourier 1D simplificada: q = -k * A * dT/dx
        return -k * area * dT / dx

