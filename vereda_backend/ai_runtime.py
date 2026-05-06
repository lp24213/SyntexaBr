from vereda_ai.ai import LLMEngine, ReasoningEngine, AgentSystem
from vereda_ai.ai.memory_system import MemorySystem
from vereda_ai.agents import Planner, Executor, TaskManager
from vereda_ai.science import MathEngine, PhysicsEngine, EngineeringEngine, SimulationEngine
from vereda_ai.memory import (
    ConversationMemory,
    EpisodicMemory,
    SemanticMemory,
    InMemoryVectorStore,
)
from vereda_ai.knowledge.rag_engine import RAGEngine
from vereda_ai.tools import MathSolver, CodeExecutor
from vereda_ai.execution import Sandbox, CodeValidator
from vereda_ai.core.logging import get_logger
from vereda_ai.reasoning import ModularReasoningEngine
from vereda_ai.cache import ResponseCache
from vereda_ai.memory.chat_history_db import ChatHistoryDB


logger = get_logger(__name__)


def _runtime_embed_batch(texts: list[str]) -> list[list[float]]:
    """Uma única porta para vetores no RAG/memória em RAM (Ollama / FastEmbed / …)."""
    from vereda_ai.syntexa_core.hybrid_engine import native_embed

    return native_embed(texts)


# Instâncias globais (singleton simples para o backend atual)
llm_engine = LLMEngine()
reasoning_engine = ReasoningEngine(llm_engine)

planner = Planner(llm_engine)
task_manager = TaskManager()

# Memória vetorial em memória, usada tanto para RAG quanto para memórias de conversa/episódica/semântica.
vector_store = InMemoryVectorStore(embed_batch_fn=_runtime_embed_batch)
conversation_memory = ConversationMemory(vector_store)
episodic_memory = EpisodicMemory(vector_store)
semantic_memory = SemanticMemory(vector_store)
memory_system = MemorySystem(vector_store)

# RAG engine conectado ao mesmo vector store e ao LLM.
rag_engine = RAGEngine(llm_engine, vector_store)

math_engine = MathEngine()
physics_engine = PhysicsEngine()
engineering_engine = EngineeringEngine()
simulation_engine = SimulationEngine()

math_solver = MathSolver()
code_executor = CodeExecutor()

sandbox = Sandbox()
code_validator = CodeValidator()

# Arquitetura modular: router + agentes + tools + cache
response_cache = ResponseCache(ttl_seconds=300)
chat_history_db = ChatHistoryDB()
modular_engine = ModularReasoningEngine(llm=llm_engine, rag=rag_engine, cache=response_cache)
executor = Executor(llm=llm_engine, modular_engine=modular_engine)
agent_system = AgentSystem(planner, executor, task_manager)


def init_runtime() -> None:
    logger.info("AI runtime inicializado (LLM, agentes, memória, ciência).")

