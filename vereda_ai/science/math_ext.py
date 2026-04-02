# -*- coding: utf-8 -*-
"""
Extended math capabilities: linear algebra, probability, number theory.
Uses SymPy + NumPy; lightweight for CPU.
"""
from typing import Any, List, Optional, Union

import numpy as np


def linear_algebra_det(A: List[List[float]]) -> float:
    """Determinant of matrix A."""
    return float(np.linalg.det(A))


def linear_algebra_inv(A: List[List[float]]) -> List[List[float]]:
    """Inverse of matrix A."""
    arr = np.array(A)
    inv = np.linalg.inv(arr)
    return inv.tolist()


def linear_algebra_eigenvalues(A: List[List[float]]) -> List[Union[float, complex]]:
    """Eigenvalues of matrix A."""
    w, _ = np.linalg.eig(np.array(A))
    return [complex(x).real if abs(complex(x).imag) < 1e-10 else complex(x) for x in w]


def probability_binomial(n: int, k: int, p: float) -> float:
    """P(X=k) for Binomial(n, p)."""
    from scipy import stats
    return float(stats.binom.pmf(k, n, p))


def probability_normal_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """CDF of Normal(mu, sigma) at x."""
    from scipy import stats
    return float(stats.norm.cdf(x, loc=mu, scale=sigma))


def number_theory_gcd(a: int, b: int) -> int:
    """Greatest common divisor."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def number_theory_is_prime(n: int) -> bool:
    """Primality test (trial division). Suitable for moderate n."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def number_theory_mod_inverse(a: int, m: int) -> Optional[int]:
    """Modular inverse of a mod m (if exists)."""
    def extended_gcd(a: int, b: int):
        if a == 0:
            return b, 0, 1
        g, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return g, x, y
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        return None
    return (x % m + m) % m


class MathEngineExt:
    """
    Extended math engine: linear algebra, probability, number theory.
    Complements existing MathEngine (symbolic + numeric).
    """

    def __init__(self) -> None:
        pass

    def det(self, A: List[List[float]]) -> float:
        return linear_algebra_det(A)

    def inv(self, A: List[List[float]]) -> List[List[float]]:
        return linear_algebra_inv(A)

    def eigenvalues(self, A: List[List[float]]) -> List[Union[float, complex]]:
        return linear_algebra_eigenvalues(A)

    def binom_pmf(self, n: int, k: int, p: float) -> float:
        return probability_binomial(n, k, p)

    def normal_cdf(self, x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
        return probability_normal_cdf(x, mu, sigma)

    def gcd(self, a: int, b: int) -> int:
        return number_theory_gcd(a, b)

    def is_prime(self, n: int) -> bool:
        return number_theory_is_prime(n)

    def mod_inverse(self, a: int, m: int) -> Optional[int]:
        return number_theory_mod_inverse(a, m)
