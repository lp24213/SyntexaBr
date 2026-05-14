"""
VEREDA / SYNTEXA — Core LLM Engine
===================================
Motor de inferência soberano completo para LLM proprietária.
"""

from .engine import VeredaInferenceEngine
from .tokenizer import VeredaTokenizer
from .kv_cache import KVCacheManager
from .context import ContextManager
from .streamer import TokenStreamer
from .scheduler import GPUScheduler
from .batching import DynamicBatcher
from .memory_compressor import MemoryCompressor
from .prompt_optimizer import PromptOptimizer
from .router import SemanticRouter

__all__ = [
    "VeredaInferenceEngine",
    "VeredaTokenizer",
    "KVCacheManager",
    "ContextManager",
    "TokenStreamer",
    "GPUScheduler",
    "DynamicBatcher",
    "MemoryCompressor",
    "PromptOptimizer",
    "SemanticRouter",
]
