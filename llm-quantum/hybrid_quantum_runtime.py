"""
SYNTEXA HYBRID QUANTUM RUNTIME
================================
Runtime híbrido que integra Foundation Model neural com camada quântica QPanda3.
Usa circuitos variacionais para otimização de sampling e otimização de hiperparâmetros.
"""
from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from llm_quantum.quantum_scheduler import QuantumScheduler, TaskType, TaskPriority

log = logging.getLogger(__name__)


try:
    from pyqpanda import CPUQVM, QProg, H, RX, RY, RZ, CNOT, Measure
    QPANDA_AVAILABLE = True
except ImportError:
    QPANDA_AVAILABLE = False
    log.warning("pyqpanda não disponível — hybrid runtime usará simulação clássica")


class HybridQuantumRuntime:
    """
    Runtime híbrido neural-quântico da Syntexa.
    Integra-se à Foundation Model para:
    1. Otimização de sampling via amostragem quântica
    2. Otimização de hiperparâmetros (temperature, top_p) via circuito variacional
    3. Pesquisa em espaço de estados com aceleração quântica
    """

    def __init__(self, n_qubits: int = 8, use_quantum: bool = True):
        self.n_qubits = n_qubits
        self.use_quantum = use_quantum and QPANDA_AVAILABLE
        self.scheduler = QuantumScheduler(use_quantum=self.use_quantum)
        self._vm: Optional[Any] = None
        self._variational_params: List[float] = [random.uniform(-math.pi, math.pi) for _ in range(n_qubits * 2)]

        if self.use_quantum:
            self._init_qpanda()

    def _init_qpanda(self) -> None:
        try:
            self._vm = CPUQVM()
            self._vm.init_qvm()
            log.info("[HybridQuantumRuntime] QPanda CPUQVM inicializado (%d qubits)", self.n_qubits)
        except Exception as e:
            log.error("[HybridQuantumRuntime] Falha QPanda: %s", e)
            self.use_quantum = False

    # ── QUANTUM SAMPLING FOR TOKEN GENERATION ─────────────────

    def quantum_sample_logits(
        self,
        logits: np.ndarray,
        temperature: float = 1.0,
        top_p: float = 0.9,
    ) -> int:
        """
        Usa circuito quântico para amostrar token a partir de distribuição de logits.
        Codifica probabilidades em estados quânticos e mede para obter amostra.
        """
        if not self.use_quantum or self._vm is None:
            return self._classical_sample(logits, temperature, top_p)

        # Normaliza logits para probabilidades
        probs = self._logits_to_probs(logits, temperature, top_p)
        n_states = min(len(probs), 2 ** self.n_qubits)
        probs = probs[:n_states]
        probs = probs / probs.sum()

        # Constrói circuito que prepara superposição ponderada pelas probabilidades
        q = self._vm.qAlloc_many(self.n_qubits)
        c = self._vm.cAlloc_many(self.n_qubits)
        prog = QProg()

        # Aplica rotações de ângulo baseadas nas probabilidades (encoding amplitude simplificado)
        for i in range(min(self.n_qubits, int(math.log2(n_states)))):
            angle = math.asin(math.sqrt(probs[i] if i < len(probs) else 0.0)) * 2
            prog.insert(RY(q[i], angle))

        # Entrelaçamento
        for i in range(self.n_qubits - 1):
            prog.insert(CNOT(q[i], q[i + 1]))

        # Medição
        for i in range(self.n_qubits):
            prog.insert(Measure(q[i], c[i]))

        result = self._vm.run_with_configuration(prog, c, 1024)
        most_likely = max(result, key=result.get) if result else "0" * self.n_qubits
        idx = int(most_likely, 2)
        return min(idx, len(logits) - 1)

    def _classical_sample(self, logits: np.ndarray, temperature: float, top_p: float) -> int:
        """Fallback clássico para sampling."""
        import torch
        import torch.nn.functional as F
        if isinstance(logits, np.ndarray):
            logits = torch.from_numpy(logits)
        logits = logits / max(temperature, 1e-5)
        probs = F.softmax(logits, dim=-1).numpy()
        # Top-p filtering
        sorted_probs = np.sort(probs)[::-1]
        cumsum = np.cumsum(sorted_probs)
        cutoff = sorted_probs[np.searchsorted(cumsum, top_p)]
        probs = np.where(probs < cutoff, 0, probs)
        probs = probs / probs.sum()
        return np.random.choice(len(probs), p=probs)

    def _logits_to_probs(self, logits: np.ndarray, temperature: float, top_p: float) -> np.ndarray:
        """Converte logits para probabilidades filtradas por top-p."""
        import torch
        import torch.nn.functional as F
        if isinstance(logits, np.ndarray):
            logits = torch.from_numpy(logits)
        logits = logits / max(temperature, 1e-5)
        probs = F.softmax(logits, dim=-1).numpy()
        sorted_probs = np.sort(probs)[::-1]
        cumsum = np.cumsum(sorted_probs)
        cutoff = sorted_probs[np.searchsorted(cumsum, top_p)]
        probs = np.where(probs < cutoff, 0, probs)
        return probs / probs.sum()

    # ── VARIATIONAL QUANTUM OPTIMIZER ─────────────────────────

    def optimize_hyperparameters(
        self,
        loss_history: List[float],
        current_lr: float = 3e-4,
        current_temp: float = 0.7,
    ) -> Dict[str, float]:
        """
        Usa circuito variacional quântico para otimizar hiperparâmetros.
        Codifica histórico de loss e retorna lr e temperature otimizados.
        """
        if not self.use_quantum or self._vm is None:
            return self._classical_optimize(loss_history, current_lr, current_temp)

        n_params = min(len(loss_history), self.n_qubits)
        normalized_loss = [(l - min(loss_history)) / (max(loss_history) - min(loss_history) + 1e-8) for l in loss_history[-n_params:]]

        q = self._vm.qAlloc_many(self.n_qubits)
        c = self._vm.cAlloc_many(self.n_qubits)
        prog = QProg()

        # Encoding dos losses em rotações
        for i, loss in enumerate(normalized_loss):
            angle = loss * math.pi * 2
            prog.insert(RY(q[i], angle))

        # Variational layers
        for layer in range(2):
            for i in range(self.n_qubits):
                prog.insert(RZ(q[i], self._variational_params[i * 2]))
                prog.insert(RX(q[i], self._variational_params[i * 2 + 1]))
            for i in range(self.n_qubits - 1):
                prog.insert(CNOT(q[i], q[i + 1]))

        for i in range(self.n_qubits):
            prog.insert(Measure(q[i], c[i]))

        result = self._vm.run_with_configuration(prog, c, 1024)
        most_likely = max(result, key=result.get) if result else "0" * self.n_qubits
        bitstring = most_likely

        # Decodifica bitstring para hiperparâmetros
        lr_factor = int(bitstring[:4], 2) / 15.0  # 0-1
        temp_factor = int(bitstring[4:8], 2) / 15.0 if len(bitstring) >= 8 else 0.5

        new_lr = current_lr * (0.5 + lr_factor)  # range: 0.5x to 1.5x
        new_temp = 0.3 + temp_factor * 1.2  # range: 0.3 to 1.5

        return {
            "learning_rate": round(new_lr, 6),
            "temperature": round(new_temp, 2),
            "bitstring": bitstring,
            "backend": "qpanda3",
        }

    def _classical_optimize(self, loss_history: List[float], current_lr: float, current_temp: float) -> Dict[str, float]:
        """Otimização clássica de hiperparâmetros."""
        if len(loss_history) < 2:
            return {"learning_rate": current_lr, "temperature": current_temp, "backend": "classical"}
        recent_trend = loss_history[-1] - loss_history[-5] if len(loss_history) >= 5 else loss_history[-1] - loss_history[0]
        if recent_trend > 0:  # loss aumentando
            new_lr = current_lr * 0.95
            new_temp = min(1.0, current_temp * 1.05)
        else:
            new_lr = current_lr * 1.02
            new_temp = max(0.3, current_temp * 0.98)
        return {
            "learning_rate": round(new_lr, 6),
            "temperature": round(new_temp, 2),
            "backend": "classical",
        }

    # ── QUANTUM STATE SEARCH ──────────────────────────────────

    def quantum_state_search(
        self,
        embeddings: np.ndarray,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        Usa amplitudes quânticas para acelerar busca por similaridade em embeddings.
        Codifica query e documentos em estados quânticos.
        """
        if not self.use_quantum or self._vm is None or len(embeddings) > 2 ** self.n_qubits:
            return self._classical_search(embeddings, query_embedding, top_k)

        # Normaliza
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        doc_norms = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

        n_docs = min(len(embeddings), 2 ** self.n_qubits)
        similarities = np.dot(doc_norms[:n_docs], query_norm)

        # Codifica similaridades em amplitudes
        q = self._vm.qAlloc_many(self.n_qubits)
        c = self._vm.cAlloc_many(self.n_qubits)
        prog = QProg()

        for i in range(min(self.n_qubits, int(math.log2(n_docs)))):
            sim = similarities[i] if i < len(similarities) else 0.0
            angle = math.asin(max(-1.0, min(1.0, sim))) * 2
            prog.insert(RY(q[i], angle))

        for i in range(self.n_qubits - 1):
            prog.insert(CNOT(q[i], q[i + 1]))

        for i in range(self.n_qubits):
            prog.insert(Measure(q[i], c[i]))

        result = self._vm.run_with_configuration(prog, c, 2048)
        outcomes = sorted(result.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(int(bits, 2), count / 2048.0) for bits, count in outcomes if int(bits, 2) < n_docs]

    def _classical_search(self, embeddings: np.ndarray, query_embedding: np.ndarray, top_k: int) -> List[Tuple[int, float]]:
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        doc_norms = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
        similarities = np.dot(doc_norms, query_norm)
        top_indices = np.argsort(-similarities)[:top_k]
        return [(int(i), float(similarities[i])) for i in top_indices]

    # ── INTEGRATION WITH FOUNDATION MODEL ───────────────────────

    def enhance_generation(
        self,
        logits: np.ndarray,
        generation_step: int,
        loss_history: Optional[List[float]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Melhora geração de tokens usando camada quântica.
        Retorna token escolhido + metadados.
        """
        # Ajusta temperature dinamicamente se houver histórico de loss
        if loss_history and generation_step % 10 == 0:
            hyperparams = self.optimize_hyperparameters(loss_history)
            temperature = hyperparams["temperature"]
        else:
            temperature = 0.7

        # Sampling quântico
        token_id = self.quantum_sample_logits(logits, temperature=temperature)

        metadata = {
            "temperature": temperature,
            "quantum_used": self.use_quantum,
            "generation_step": generation_step,
        }

        return token_id, metadata

    def shutdown(self) -> None:
        self.scheduler.shutdown()
        if self._vm and QPANDA_AVAILABLE:
            self._vm.finalize()
        log.info("[HybridQuantumRuntime] Shutdown completo")
