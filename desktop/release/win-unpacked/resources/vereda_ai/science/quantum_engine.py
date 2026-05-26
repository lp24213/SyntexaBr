# -*- coding: utf-8 -*-
"""
Lightweight quantum simulation using Qiskit (optional). Simulate qubits and basic gates.
Install: pip install qiskit qiskit-aer
"""
from typing import Any, List, Optional

_has_qiskit = False
try:
    import qiskit
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    _has_qiskit = True
except ImportError:
    pass


def quantum_available() -> bool:
    return _has_qiskit


def quantum_simulate_circuit(
    num_qubits: int = 2,
    gates: Optional[List[tuple]] = None,
    shots: int = 1024,
) -> Optional[dict]:
    """
    Build a simple circuit and run simulation. gates: list of ("H", 0), ("CX", 0, 1), etc.
    Returns counts dict or None if Qiskit not available.
    """
    if not _has_qiskit:
        return None
    try:
        qc = QuantumCircuit(num_qubits, num_qubits)
        gates = gates or [("H", 0), ("CX", 0, 1)]
        for g in gates:
            name = g[0].upper()
            if name == "H":
                qc.h(g[1])
            elif name == "X":
                qc.x(g[1])
            elif name == "Y":
                qc.y(g[1])
            elif name == "Z":
                qc.z(g[1])
            elif name == "CX" and len(g) >= 3:
                qc.cx(g[1], g[2])
            elif name == "CZ" and len(g) >= 3:
                qc.cz(g[1], g[2])
        qc.measure(range(num_qubits), range(num_qubits))
        sim = AerSimulator()
        t = transpile(qc, sim)
        job = sim.run(t, shots=shots)
        return dict(job.result().get_counts())
    except Exception:
        return None


def quantum_bell_state(shots: int = 1024) -> Optional[dict]:
    """Create Bell state (|00> + |11>)/sqrt(2) and measure."""
    return quantum_simulate_circuit(
        num_qubits=2,
        gates=[("H", 0), ("CX", 0, 1)],
        shots=shots,
    )


class QuantumEngine:
    """
    Lightweight quantum simulation engine. Requires qiskit and qiskit-aer.
    """

    def __init__(self) -> None:
        self._available = quantum_available()

    @property
    def available(self) -> bool:
        return self._available

    def simulate(
        self,
        num_qubits: int = 2,
        gates: Optional[List[tuple]] = None,
        shots: int = 1024,
    ) -> Optional[dict]:
        return quantum_simulate_circuit(num_qubits=num_qubits, gates=gates, shots=shots)

    def bell_state(self, shots: int = 1024) -> Optional[dict]:
        return quantum_bell_state(shots=shots)
