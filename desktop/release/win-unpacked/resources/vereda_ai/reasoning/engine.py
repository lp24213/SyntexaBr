# -*- coding: utf-8 -*-
"""
Engine de raciocínio modular: Router -> Agent -> Tools -> Resposta final.
Decomposição de problema, execução de tools, geração de resposta.
"""
from typing import Any, Dict, Optional

from vereda_ai.router.prompt_router import PromptRouter, RouteCategory
from vereda_ai.agents.math_agent import MathAgent
from vereda_ai.agents.code_agent import CodeAgent
from vereda_ai.agents.knowledge_agent import KnowledgeAgent
from vereda_ai.agents.vision_agent import VisionAgent
from vereda_ai.agents.crypto_agent import CryptoAgent
from vereda_ai.agents.general_agent import GeneralAgent
from vereda_ai.cache.response_cache import ResponseCache


class ModularReasoningEngine:
    """
    Fluxo: User Prompt -> Router -> Agent -> (Tools) -> ReasoningEngine -> Resposta.
    Otimizado para baixo consumo de memória e CPU.
    """

    def __init__(
        self,
        llm=None,
        rag=None,
        cache: Optional[ResponseCache] = None,
    ):
        self.llm = llm
        self.rag = rag
        self.cache = cache or ResponseCache(ttl_seconds=300)
        self.router = PromptRouter()
        self.agents = {
            RouteCategory.MATH: MathAgent(llm=llm),
            RouteCategory.CODE: CodeAgent(llm=llm),
            RouteCategory.KNOWLEDGE: KnowledgeAgent(llm=llm, rag=rag),
            RouteCategory.VISION: VisionAgent(llm=llm),
            RouteCategory.CRYPTO: CryptoAgent(llm=llm),
            RouteCategory.WEB: GeneralAgent(llm=llm),
            RouteCategory.GENERAL: GeneralAgent(llm=llm),
        }

    def process(
        self,
        prompt: str,
        user_id: str = "anon",
        history: Optional[list] = None,
        knowledge_snippets: Optional[list] = None,
        memory_snippets: Optional[list] = None,
        image_data: Optional[bytes] = None,
        image_path: Optional[str] = None,
        use_cache: bool = True,
    ) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            return "Envie uma mensagem."

        if use_cache:
            cached = self.cache.get(prompt, user_id)
            if cached is not None:
                return cached

        context: Dict[str, Any] = {
            "user_id": user_id,
            "history": history or [],
            "knowledge_snippets": knowledge_snippets or [],
            "memory_snippets": memory_snippets or [],
            "image_data": image_data,
            "image_path": image_path,
        }

        category = self.router.route(prompt)
        agent = self.agents.get(category) or self.agents[RouteCategory.GENERAL]
        try:
            response = agent.handle(prompt, context)
        except Exception as e:
            response = "Erro ao processar: %s." % e

        if use_cache and response:
            self.cache.set(prompt, response, user_id)
        return response
