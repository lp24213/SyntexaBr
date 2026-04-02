# -*- coding: utf-8 -*-
"""
Modos Syntexa implementados em código: MODO COPILOTO e MODO LAB.
Cada modo é um pipeline que monta instruções estruturadas e usa o LLM.
"""
from typing import Optional, Any, List
import re


def detect_mode(content: str) -> Optional[str]:
    """Detecta modo ativado pelo usuário (código próprio): copiloto, lab, cientifico, juridico, estrategico."""
    if not content or not isinstance(content, str):
        return None
    t = content.strip().upper()
    t_compact = t.replace(" ", "")
    if "MODOCOPILOTO" in t_compact or "MODO COPILOTO" in t:
        return "copiloto"
    if "MODOLAB" in t_compact or "MODO LAB" in t or "MODO LABORATÓRIO" in t:
        return "lab"
    if "MODO CIENTÍFICO" in t or "MODOCIENTÍFICO" in t_compact or "MODO CIENTIFICO" in t:
        return "cientifico"
    if "MODO JURÍDICO" in t or "MODOJURÍDICO" in t_compact or "MODO JURIDICO" in t or "MODOJURIDICO" in t_compact:
        return "juridico"
    if "MODO ESTRATÉGICO" in t or "MODOESTRATÉGICO" in t_compact or "MODO ESTRATEGICO" in t or "MODOESTRATEGICO" in t_compact:
        return "estrategico"
    return None


def _strip_mode_trigger(content: str, mode: str) -> str:
    """Remove a frase que ativou o modo para extrair o tema/pergunta."""
    patterns = [
        r"^\s*MODO\s*COPILOTO\s*[:\-]?\s*",
        r"^\s*MODO\s*LAB(ORATÓRIO)?\s*[:\-]?\s*",
        r"^\s*MODOCOPILOTO\s*[:\-]?\s*",
        r"^\s*MODOLAB\s*[:\-]?\s*",
        r"^\s*MODO\s*CIENT[ÍI]FICO\s*[:\-]?\s*",
        r"^\s*MODO\s*JUR[ÍI]DICO\s*[:\-]?\s*",
        r"^\s*MODO\s*ESTRAT[ÉE]GICO\s*[:\-]?\s*",
    ]
    out = content.strip()
    for p in patterns:
        out = re.sub(p, "", out, flags=re.IGNORECASE).strip()
    return out or "assunto geral"


# Instruções estruturadas por modo (código próprio, não prompt solto)
COPILOTO_SYSTEM = """Você está no MODO COPILOTO da Syntexa. Comportamento obrigatório:
1. Pense como arquiteto técnico.
2. Quebre o problema em módulos claros.
3. Defina stack recomendada (tecnologias concretas).
4. Aponte riscos técnicos.
5. Sugira um roadmap de desenvolvimento (fases/entregas).
Responda de forma estruturada, técnica e direta. Use tópicos ou seções quando fizer sentido."""

LAB_SYSTEM = """Você está no MODO LABORATÓRIO da Syntexa. Comportamento obrigatório:
1. Estruture uma ou mais hipóteses.
2. Defina variáveis (dependentes e independentes).
3. Indique métodos científicos adequados.
4. Proponha experimentos controlados e reprodutíveis.
Use linguagem de pesquisa. Diferencie fato de suposição."""

CIENTIFICO_SYSTEM = """Você está no MODO CIENTÍFICO da Syntexa. Aplique o método:
1. Hipótese.
2. Revisão bibliográfica.
3. Evidência.
4. Limitações.
5. Conclusão.
Priorize fontes revisadas por pares. Indique nível de confiabilidade."""

JURIDICO_SYSTEM = """Você está no MODO JURÍDICO da Syntexa. Comportamento obrigatório:
• Citar legislação vigente.
• Indicar se é jurisprudência consolidada ou decisão isolada.
• Deixar claro: análise técnica; não substitui advogado.
Estruture: fontes (lei/jurisprudência) | análise | conclusão."""

ESTRATEGICO_SYSTEM = """Você está no MODO ESTRATÉGICO da Syntexa. Avalie:
• Impacto macroeconômico.
• Risco geopolítico.
• Viabilidade técnica.
Apresente múltiplas perspectivas quando houver incerteza. Seja objetivo na conclusão."""


def run_copiloto(
    user_query: str,
    llm_engine: Any,
    history: Optional[List[dict]] = None,
    temperature: float = 0.5,
    max_tokens: int = 1024,
) -> str:
    """Pipeline MODO COPILOTO: arquitetura, módulos, stack, riscos, roadmap (código próprio)."""
    theme = _strip_mode_trigger(user_query, "copiloto")
    messages = [
        {"role": "system", "content": COPILOTO_SYSTEM},
        {"role": "user", "content": f"Tema ou problema: {theme}\n\nAnalise no modo copiloto (módulos, stack, riscos, roadmap)."},
    ]
    if history:
        for m in history[-6:]:
            messages.insert(-1, {"role": m.get("role", "user"), "content": m.get("content", "")[:2000]})
    return llm_engine.chat(messages, temperature=temperature, max_tokens=max_tokens)


def run_lab(
    user_query: str,
    llm_engine: Any,
    history: Optional[List[dict]] = None,
    temperature: float = 0.4,
    max_tokens: int = 1024,
) -> str:
    """Pipeline MODO LAB: hipóteses, variáveis, métodos, experimentos (código próprio)."""
    theme = _strip_mode_trigger(user_query, "lab")
    messages = [
        {"role": "system", "content": LAB_SYSTEM},
        {"role": "user", "content": f"Tema ou pergunta: {theme}\n\nEstruture no modo laboratório (hipóteses, variáveis, métodos, experimentos)."},
    ]
    if history:
        for m in history[-6:]:
            messages.insert(-1, {"role": m.get("role", "user"), "content": m.get("content", "")[:2000]})
    return llm_engine.chat(messages, temperature=temperature, max_tokens=max_tokens)


def run_cientifico(
    user_query: str,
    llm_engine: Any,
    history: Optional[List[dict]] = None,
    temperature: float = 0.4,
    max_tokens: int = 1024,
) -> str:
    """Pipeline MODO CIENTÍFICO: hipótese, revisão, evidência, limitações, conclusão."""
    theme = _strip_mode_trigger(user_query, "cientifico")
    messages = [
        {"role": "system", "content": CIENTIFICO_SYSTEM},
        {"role": "user", "content": f"Tema ou pergunta: {theme}\n\nEstruture no modo científico (hipótese, revisão bibliográfica, evidência, limitações, conclusão)."},
    ]
    if history:
        for m in history[-6:]:
            messages.insert(-1, {"role": m.get("role", "user"), "content": m.get("content", "")[:2000]})
    return llm_engine.chat(messages, temperature=temperature, max_tokens=max_tokens)


def run_juridico(
    user_query: str,
    llm_engine: Any,
    history: Optional[List[dict]] = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """Pipeline MODO JURÍDICO: legislação vigente, jurisprudência, análise técnica."""
    theme = _strip_mode_trigger(user_query, "juridico")
    messages = [
        {"role": "system", "content": JURIDICO_SYSTEM},
        {"role": "user", "content": f"Tema ou questão: {theme}\n\nResponda no modo jurídico (cite legislação, indique jurisprudência consolidada ou isolada)."},
    ]
    if history:
        for m in history[-6:]:
            messages.insert(-1, {"role": m.get("role", "user"), "content": m.get("content", "")[:2000]})
    return llm_engine.chat(messages, temperature=temperature, max_tokens=max_tokens)


def run_estrategico(
    user_query: str,
    llm_engine: Any,
    history: Optional[List[dict]] = None,
    temperature: float = 0.5,
    max_tokens: int = 1024,
) -> str:
    """Pipeline MODO ESTRATÉGICO: impacto macroeconômico, risco geopolítico, viabilidade técnica."""
    theme = _strip_mode_trigger(user_query, "estrategico")
    messages = [
        {"role": "system", "content": ESTRATEGICO_SYSTEM},
        {"role": "user", "content": f"Tema ou cenário: {theme}\n\nAvalie no modo estratégico (macroeconomia, risco geopolítico, viabilidade técnica)."},
    ]
    if history:
        for m in history[-6:]:
            messages.insert(-1, {"role": m.get("role", "user"), "content": m.get("content", "")[:2000]})
    return llm_engine.chat(messages, temperature=temperature, max_tokens=max_tokens)
