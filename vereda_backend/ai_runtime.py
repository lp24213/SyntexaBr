"""AI Runtime — LAZY LOADING. NÃO carrega modelos no import.

Em modo gateway (Railway), as bibliotecas pesadas podem não estar instaladas.
O código abaixo usa lazy factories para criar instâncias sob demanda.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Lazy factory registry ──
_registry: dict[str, Any] = {}


def _lazy(name: str, factory) -> Any:
    if name not in _registry:
        try:
            _registry[name] = factory()
        except Exception as exc:
            logger.warning("Lazy load %s failed: %s", name, exc)
            raise
    return _registry[name]


# ── Embeddings via proxy (gateway mode) ou local ──
def _runtime_embed_batch(texts: list[str]) -> list[list[float]]:
    from vereda_backend.core.config import settings
    if settings.ai_worker_url:
        from vereda_backend.core.ai_proxy_client import proxy_embeddings_sync
        try:
            result = proxy_embeddings_sync(texts)
            return result.get("data", [])
        except Exception as exc:
            logger.warning("Proxy embed failed: %s", exc)
    try:
        from vereda_ai.syntexa_core.hybrid_engine import native_embed
        return native_embed(texts)
    except Exception as exc:
        logger.warning("native_embed failed: %s", exc)
        return []


# ── Factories para instâncias de IA ──
def _make_llm_engine():
    from vereda_ai.ai import LLMEngine
    return LLMEngine()


def _make_reasoning_engine():
    from vereda_ai.ai import ReasoningEngine
    return ReasoningEngine(llm_engine)


def _make_planner():
    from vereda_ai.agents import Planner
    return Planner(llm_engine)


def _make_task_manager():
    from vereda_ai.agents import TaskManager
    return TaskManager()


def _make_vector_store():
    from vereda_ai.memory import InMemoryVectorStore
    return InMemoryVectorStore(embed_batch_fn=_runtime_embed_batch)


def _make_conversation_memory():
    from vereda_ai.memory import ConversationMemory
    return ConversationMemory(vector_store)


def _make_episodic_memory():
    from vereda_ai.memory import EpisodicMemory
    return EpisodicMemory(vector_store)


def _make_semantic_memory():
    from vereda_ai.memory import SemanticMemory
    return SemanticMemory(vector_store)


def _make_memory_system():
    from vereda_ai.ai.memory_system import MemorySystem
    return MemorySystem(vector_store)


def _make_rag_engine():
    from vereda_ai.knowledge.rag_engine import RAGEngine
    return RAGEngine(llm_engine, vector_store)


def _make_math_engine():
    from vereda_ai.science import MathEngine
    return MathEngine()


def _make_physics_engine():
    from vereda_ai.science import PhysicsEngine
    return PhysicsEngine()


def _make_engineering_engine():
    from vereda_ai.science import EngineeringEngine
    return EngineeringEngine()


def _make_simulation_engine():
    from vereda_ai.science import SimulationEngine
    return SimulationEngine()


def _make_math_solver():
    from vereda_ai.tools import MathSolver
    return MathSolver()


def _make_code_executor():
    from vereda_ai.tools import CodeExecutor
    return CodeExecutor()


def _make_sandbox():
    from vereda_ai.execution import Sandbox
    return Sandbox()


def _make_code_validator():
    from vereda_ai.execution import CodeValidator
    return CodeValidator()


def _make_response_cache():
    from vereda_ai.cache import ResponseCache
    return ResponseCache(ttl_seconds=300)


def _make_chat_history_db():
    from vereda_ai.memory.chat_history_db import ChatHistoryDB
    return ChatHistoryDB()


def _make_modular_engine():
    from vereda_ai.reasoning import ModularReasoningEngine
    return ModularReasoningEngine(llm=llm_engine, rag=rag_engine, cache=response_cache)


def _make_executor():
    from vereda_ai.agents import Executor
    return Executor(llm=llm_engine, modular_engine=modular_engine)


def _make_agent_system():
    from vereda_ai.agents import AgentSystem
    return AgentSystem(planner, executor, task_manager)


# ── LazyObject: proxy que só resolve a instância real no primeiro uso ──
class LazyObject:
    """Proxy transparente que adia a criação do objeto até o primeiro acesso."""

    __slots__ = ("_name", "_factory", "_instance", "_resolved")

    def __init__(self, name: str, factory):
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_instance", None)
        object.__setattr__(self, "_resolved", False)

    def _resolve(self):
        if not object.__getattribute__(self, "_resolved"):
            instance = object.__getattribute__(self, "_factory")()
            object.__setattr__(self, "_instance", instance)
            object.__setattr__(self, "_resolved", True)
        return object.__getattribute__(self, "_instance")

    def __getattr__(self, item):
        return getattr(self._resolve(), item)

    def __setattr__(self, key, value):
        setattr(self._resolve(), key, value)

    def __call__(self, *args, **kwargs):
        return self._resolve()(*args, **kwargs)

    def __getitem__(self, item):
        return self._resolve()[item]

    def __setitem__(self, key, value):
        self._resolve()[key] = value

    def __contains__(self, item):
        return item in self._resolve()

    def __iter__(self):
        return iter(self._resolve())

    def __len__(self):
        return len(self._resolve())

    def __bool__(self):
        return bool(self._resolve())

    def __str__(self):
        return str(self._resolve())

    def __repr__(self):
        return repr(self._resolve())

    def __eq__(self, other):
        return self._resolve() == other

    def __ne__(self, other):
        return self._resolve() != other

    def __hash__(self):
        return hash(self._resolve())


# ── Singleton proxies ──
# `from vereda_backend.ai_runtime import llm_engine` retorna um LazyObject.
# A instância real só é criada quando alguém chama `llm_engine.gerar(...)` etc.
llm_engine = LazyObject("llm_engine", _make_llm_engine)
reasoning_engine = LazyObject("reasoning_engine", _make_reasoning_engine)
planner = LazyObject("planner", _make_planner)
task_manager = LazyObject("task_manager", _make_task_manager)
vector_store = LazyObject("vector_store", _make_vector_store)
conversation_memory = LazyObject("conversation_memory", _make_conversation_memory)
episodic_memory = LazyObject("episodic_memory", _make_episodic_memory)
semantic_memory = LazyObject("semantic_memory", _make_semantic_memory)
memory_system = LazyObject("memory_system", _make_memory_system)
rag_engine = LazyObject("rag_engine", _make_rag_engine)
math_engine = LazyObject("math_engine", _make_math_engine)
physics_engine = LazyObject("physics_engine", _make_physics_engine)
engineering_engine = LazyObject("engineering_engine", _make_engineering_engine)
simulation_engine = LazyObject("simulation_engine", _make_simulation_engine)
math_solver = LazyObject("math_solver", _make_math_solver)
code_executor = LazyObject("code_executor", _make_code_executor)
sandbox = LazyObject("sandbox", _make_sandbox)
code_validator = LazyObject("code_validator", _make_code_validator)
response_cache = LazyObject("response_cache", _make_response_cache)
chat_history_db = LazyObject("chat_history_db", _make_chat_history_db)
modular_engine = LazyObject("modular_engine", _make_modular_engine)
executor = LazyObject("executor", _make_executor)
agent_system = LazyObject("agent_system", _make_agent_system)


def init_runtime() -> None:
    logger.info("AI runtime inicializado (LLM, agentes, memória, ciência).")

