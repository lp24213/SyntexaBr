from sympy import Matrix, diff, integrate, sympify
from sympy.core.sympify import SympifyError


class SymbolicEngine:
    """
    Álgebra simbólica: derivadas, integrais, sistemas lineares simbólicos.
    """

    def eval_expression(self, expr: str, subs: dict | None = None) -> str:
        try:
            e = sympify(expr)
            if subs:
                e = e.subs(subs)
            return str(e.simplify())
        except SympifyError as exc:
            raise ValueError(f"Expressão inválida: {exc}") from exc

    def derivative(self, expr: str, var: str) -> str:
        e = sympify(expr)
        return str(diff(e, var))

    def integral(self, expr: str, var: str) -> str:
        e = sympify(expr)
        return str(integrate(e, var))

    def solve_linear_system(self, A: list[list[float]], b: list[float]) -> str:
        matA = Matrix(A)
        vecb = Matrix(b)
        sol = matA.LUsolve(vecb)
        return str(sol)

