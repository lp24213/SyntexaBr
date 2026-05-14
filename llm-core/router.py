"""
VEREDA / SYNTEXA — Semantic Router
====================================
Roteamento semântico com:
- Intent classification
- Domain routing
- Model selection
- Load balancing
"""

import re
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class Intent(Enum):
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    CREATIVE = "creative"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"
    ANALYZE = "analyze"
    MULTIMODAL = "multimodal"
    AUTONOMOUS = "autonomous"
    SYSTEM = "system"


class Domain(Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    SCIENTIFIC = "scientific"
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    CREATIVE = "creative"
    CODE = "code"


@dataclass
class RouteDecision:
    intent: Intent
    domain: Domain
    model: str
    temperature: float
    max_tokens: int
    system_prompt: str
    requires_tools: bool
    priority: int  # 0-9, menor = mais prioritário


class SemanticRouter:
    """
    Roteador semântico que decide como processar cada request.
    """

    # Mapeamento de intent → configuração
    INTENT_CONFIG = {
        Intent.CHAT: {
            "model": "vereda-native",
            "temperature": 0.7,
            "max_tokens": 1024,
            "system": "Converse de forma natural e útil.",
            "priority": 2,
        },
        Intent.CODE: {
            "model": "vereda-code",
            "temperature": 0.2,
            "max_tokens": 2048,
            "system": "Você é um programador sênior. Escreva código limpo e eficiente.",
            "priority": 1,
        },
        Intent.REASONING: {
            "model": "vereda-native",
            "temperature": 0.3,
            "max_tokens": 2048,
            "system": "Pense passo a passo. Mostre seu raciocínio.",
            "priority": 1,
        },
        Intent.CREATIVE: {
            "model": "vereda-native",
            "temperature": 0.9,
            "max_tokens": 1536,
            "system": "Seja criativo, original e inspirador.",
            "priority": 3,
        },
        Intent.SUMMARIZE: {
            "model": "vereda-native",
            "temperature": 0.1,
            "max_tokens": 512,
            "system": "Resuma de forma clara e concisa.",
            "priority": 2,
        },
        Intent.ANALYZE: {
            "model": "vereda-native",
            "temperature": 0.2,
            "max_tokens": 1536,
            "system": "Analise criticamente e forneça insights profundos.",
            "priority": 1,
        },
        Intent.MULTIMODAL: {
            "model": "vereda-multimodal",
            "temperature": 0.5,
            "max_tokens": 1024,
            "system": "Analise imagens, áudio e documentos.",
            "priority": 1,
        },
        Intent.AUTONOMOUS: {
            "model": "vereda-native",
            "temperature": 0.4,
            "max_tokens": 2048,
            "system": "Execute tarefas de forma autônoma e eficiente.",
            "priority": 0,
        },
    }

    def __init__(self):
        self._handlers: Dict[Intent, Callable] = {}

    # ── ROUTING ──────────────────────────────────────────────
    def route(self, prompt: str, user_tier: str = "free") -> RouteDecision:
        """
        Decide roteamento para um prompt.
        """
        intent = self._classify_intent(prompt)
        domain = self._detect_domain(prompt)
        config = self.INTENT_CONFIG.get(intent, self.INTENT_CONFIG[Intent.CHAT])

        # Ajustes por tier
        max_tokens = config["max_tokens"]
        if user_tier == "admin":
            max_tokens = min(max_tokens * 2, 8192)
        elif user_tier == "paid":
            max_tokens = int(max_tokens * 1.5)

        return RouteDecision(
            intent=intent,
            domain=domain,
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=max_tokens,
            system_prompt=config["system"],
            requires_tools=intent in (Intent.CODE, Intent.ANALYZE, Intent.AUTONOMOUS),
            priority=config["priority"],
        )

    # ── INTENT CLASSIFICATION ────────────────────────────────
    def _classify_intent(self, prompt: str) -> Intent:
        prompt_lower = prompt.lower()

        # Code detection
        code_patterns = [
            r"```\w+",
            r"(?:escreva|write|gerar|generate)\s+(?:código|code|script|função|function)",
            r"\b(python|javascript|java|cpp|c#|sql|html|css|react|api)\b",
            r"\b(def |class |import |function |const |let |var )",
        ]
        if any(re.search(p, prompt_lower) for p in code_patterns):
            return Intent.CODE

        # Reasoning
        reasoning_keywords = [
            "calcule", "resolva", "explique por que", "prove que", "demonstre",
            "passo a passo", "step by step", "lógica", "razoamento", "reasoning",
        ]
        if any(k in prompt_lower for k in reasoning_keywords):
            return Intent.REASONING

        # Creative
        creative_keywords = [
            "crie", "escreva", "invente", "imagine", "história", "poema", "conto",
            "create", "write a story", "poem", "creative", "imagine",
        ]
        if any(k in prompt_lower for k in creative_keywords):
            return Intent.CREATIVE

        # Summarize
        summarize_keywords = [
            "resuma", "sumarize", "resumo", "síntese", "tldr", "summary", "summarize",
        ]
        if any(k in prompt_lower for k in summarize_keywords):
            return Intent.SUMMARIZE

        # Translate
        translate_keywords = [
            "traduza", "translate", "tradução", "em português", "em inglês", "em espanhol",
        ]
        if any(k in prompt_lower for k in translate_keywords):
            return Intent.TRANSLATE

        # Multimodal
        multimodal_keywords = [
            "imagem", "image", "foto", "picture", "áudio", "audio", "vídeo", "video",
            "documento", "pdf", "analisar arquivo", "descreva esta imagem",
        ]
        if any(k in prompt_lower for k in multimodal_keywords):
            return Intent.MULTIMODAL

        # Autonomous
        autonomous_keywords = [
            "execute", "faça isso automaticamente", "autonomamente", "autonomous",
            "task", "tarefa", "pipeline", "workflow", "agente",
        ]
        if any(k in prompt_lower for k in autonomous_keywords):
            return Intent.AUTONOMOUS

        # Analyze
        analyze_keywords = [
            "analise", "análise", "compare", "contrast", "avaliação", "evaluate",
            "crítica", "review", "pros and cons", "vantagens e desvantagens",
        ]
        if any(k in prompt_lower for k in analyze_keywords):
            return Intent.ANALYZE

        return Intent.CHAT

    # ── DOMAIN DETECTION ───────────────────────────────────────
    def _detect_domain(self, prompt: str) -> Domain:
        prompt_lower = prompt.lower()

        domains = {
            Domain.CODE: ["programação", "desenvolvimento", "software", "código", "bug", "debug"],
            Domain.SCIENTIFIC: ["ciência", "física", "química", "biologia", "matemática", "research"],
            Domain.LEGAL: ["lei", "jurídico", "contrato", "legislação", "direito", "legal"],
            Domain.MEDICAL: ["médico", "saúde", "doença", "tratamento", "diagnóstico", "symptom"],
            Domain.FINANCIAL: ["financeiro", "investimento", "bolsa", "economia", "trading", "crypto"],
            Domain.CREATIVE: ["arte", "design", "música", "literatura", "criativo", "creative"],
        }

        for domain, keywords in domains.items():
            if any(k in prompt_lower for k in keywords):
                return domain

        return Domain.GENERAL

    # ── HANDLER REGISTRATION ─────────────────────────────────
    def register_handler(self, intent: Intent, handler: Callable) -> None:
        self._handlers[intent] = handler

    def get_handler(self, intent: Intent) -> Optional[Callable]:
        return self._handlers.get(intent)
