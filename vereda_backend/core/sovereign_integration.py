"""Syntexa Sovereign AI — Integration Layer

Conecta LLM Router v2 + Quantum Orchestrator ao backend existente
sem quebrar imports ou APIs estáveis.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from vereda_backend.core.config import settings
from vereda_backend.core.llm_router_v2 import (
    IntelligentLLMRouter,
    ModelCapability,
    ModelEndpoint,
    ModelSize,
    get_router,
)
from vereda_backend.core.quantum_orchestrator import (
    QuantumDecisionEngine,
    HybridInferenceScheduler,
    get_quantum_engine,
    get_scheduler,
)

logger = logging.getLogger(__name__)

# ── Auto-register endpoints from config ──
def _auto_register_endpoints() -> None:
    """Registra endpoints configurados no .env no router inteligente."""
    router = get_router()
    
    # Ollama endpoint
    ollama_url = getattr(settings, "ollama_endpoint", None)
    if ollama_url:
        router.register(ModelEndpoint(
            name="ollama_local",
            url=ollama_url,
            size=ModelSize.MEDIUM,
            capabilities=[ModelCapability.CHAT, ModelCapability.CODING, ModelCapability.REASONING],
            gpu_required=False,
            latency_p50_ms=800.0,
        ))
    
    # Azure / remote endpoint
    azure_url = getattr(settings, "azure_tgi_endpoint", None)
    if azure_url:
        router.register(ModelEndpoint(
            name="azure_tgi",
            url=azure_url,
            size=ModelSize.LARGE,
            capabilities=[ModelCapability.CHAT, ModelCapability.CODING, ModelCapability.REASONING, ModelCapability.VISION],
            gpu_required=True,
            latency_p50_ms=1200.0,
        ))
    
    # Local model endpoint (own model stack)
    local_url = getattr(settings, "local_llm_endpoint", None)
    if local_url:
        router.register(ModelEndpoint(
            name="syntexa_native",
            url=local_url,
            size=ModelSize.SMALL,
            capabilities=[ModelCapability.CHAT, ModelCapability.REASONING],
            gpu_required=False,
            latency_p50_ms=400.0,
        ))
    
    logger.info("LLM Router v2: %d endpoints registered", len(router._endpoints))


def init_sovereign_runtime() -> None:
    """Inicializa runtime evoluído (chamar em main.py se disponível)."""
    try:
        _auto_register_endpoints()
        # Warm up quantum engine
        get_quantum_engine()
        get_scheduler()
        logger.info("Sovereign AI runtime initialized (router v2 + quantum orchestrator)")
    except Exception as e:
        logger.warning("Sovereign runtime init skipped: %s", e)


# ── Public API for chat_engine.py ──
def route_request(
    prompt: str,
    messages: Optional[List[Dict[str, Any]]] = None,
    latency_budget_ms: float = 2000.0,
) -> Dict[str, Any]:
    """Roteia requisição usando o router inteligente + quantum layer."""
    router = get_router()
    
    # Use quantum engine for final decision if available
    try:
        complexity, capabilities = router.analyze_complexity(prompt, messages)
        quantum = get_quantum_engine()
        
        models = [
            {"name": name, "latency_p50_ms": ep.latency_p50_ms,
             "success_rate": (ep.use_count - ep.error_count) / max(ep.use_count, 1),
             "capacity": 1.0 - ep.load_factor}
            for name, ep in router._endpoints.items() if ep.healthy
        ]
        
        if models:
            model_name, decision = quantum.decide_model_route(
                np.zeros(128),  # placeholder
                models,
                complexity,
            )
            
            # Override router decision with quantum-enhanced choice
            if model_name in router._endpoints:
                ep = router._endpoints[model_name]
                return {
                    "model": model_name,
                    "endpoint": ep.url,
                    "complexity": complexity,
                    "capabilities": [c.value for c in capabilities],
                    "quantum": decision,
                    "method": "quantum_enhanced",
                }
    except Exception as e:
        logger.debug("Quantum routing fallback: %s", e)
    
    # Fallback to classical router
    decision = router.route(prompt, messages, latency_budget_ms)
    return {
        "model": decision.model,
        "endpoint": decision.endpoint,
        "complexity": decision.complexity_score,
        "fallback_chain": decision.fallback_chain,
        "method": "classical",
    }


# Lazy import for numpy (optional dependency)
try:
    import numpy as np
except ImportError:
    np = None
