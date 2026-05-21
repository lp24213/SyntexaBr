"""
Motor NLP híbrido proprietário (Fase 1): intents, regras, sumarização extractiva,
embeddings determinísticos — **e** camada adicional que sintetiza quando o backend injeta
contexto da internet + base de conhecimento no prompt de sistema.

Tudo o que existia antes mantém-se; a pesquisa web agora **acrescenta** respostas factuais
quando há trechos indexados (sem remover RAG, memória ou mensagens de ajuda ao pipeline).
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Iterator
from vereda_ai.core.config import settings
from vereda_ai.syntexa_core.model_registry import get_registry
from vereda_ai.syntexa_core.runtime_model import maybe_runtime_reply, maybe_runtime_reply_stream
from vereda_ai.syntexa_core.neural_engine import is_neural_available
from vereda_ai.syntexa_core.sovereign_orchestrator import orchestrated_generate, orchestrated_generate_stream
from vereda_ai.syntexa_core.foundation_runtime import (
    is_foundation_available,
    foundation_generate,
    foundation_generate_stream,
)

# Intents fixos (expandir em model_registry / datasets)
# Alinhado a `vereda_backend.core.deep_run` (evita importar o backend daqui).
_DEEP_USER_TRIGGERS = re.compile(
    r"detalh|profund|exaustiv|complet[ao]\b|passo a passo|tutorial|aprofund|"
    r"disserta|mestrado|doutorado|\bphd\b|peer[- ]?review|formalmente|demonstra[cç][aã]o|"
    r"linha a linha|white[- ]?paper|relat[oó]rio.{0,10}(longo|extenso)|"
    r"roadmap t[eé]cnico|especifica[cç][aã]o (completa|detalhada)|nível expert|"
    r"biblio|monografia|\btcc\b|tese acad|cap[ií]tulo a cap[ií]tulo|fontes prim[aá]rias?|"
    r"revis[aã]o sistem[aá]tica|meta[- ]?an[aá]lise|artigo cient[ií]fico completo|"
    r"elabora[cç][aã]o did[aá]tica|s[uú]mula completa|coment[aá]rio (de texto|exaustivo)|"
    r"\bwiki\b.{0,8}(completa|longa)|documenta[cç][aã]o (t[eé]cnica )?completa",
    re.I,
)

_INTENT_PATTERNS: list[tuple[str, list[re.Pattern[str]]]] = [
    (
        "saudacao",
        [
            re.compile(r"^(oi|olá|ola|bom dia|boa tarde|boa noite|hey|e aí|e ai)\b", re.I),
            re.compile(r"\b(hello|hi)\b", re.I),
        ],
    ),
    (
        "ajuda",
        [
            re.compile(r"\b(ajuda|help|como (funciona|usar)|o que (você|vc) (faz|faz\?))\b", re.I),
        ],
    ),
    (
        "codigo",
        [
            re.compile(r"\b(código|codigo|python|javascript|debug|erro|stack|api|endpoint)\b", re.I),
        ],
    ),
    (
        "matematica",
        [
            re.compile(r"[0-9]+\s*[\+\-\*/^]\s*[0-9]+"),
            re.compile(r"\b(calcular|quanto é|raiz|porcentagem|equação|equacao)\b", re.I),
        ],
    ),
]


def _last_user_text(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        if (m.get("role") or "").lower() == "user":
            return (m.get("content") or "").strip()
    return ""


def _gather_system_text(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for m in messages:
        if (m.get("role") or "").lower() == "system":
            c = (m.get("content") or "").strip()
            if c:
                parts.append(c)
    return "\n\n".join(parts)


# Só existem no prompt quando o backend injeta conteúdo real (ver `build_system_prompt_from_identity`).
_WEB_INJECT_HEAD = "Contexto da web (dados reais da internet"
_WEB_CONTENT_AFTER = "quando estiverem presentes:\n"
_REF_HDR = "Referências consultadas (liste ou cite quando usar fatos delas; não invente URLs):\n"
_KB_HDR = "Base de conhecimento relevante:"


def _extract_kb_block(system: str) -> str:
    """Trechos da base só entre o cabeçalho injetado e as secções seguintes (nunca o resto do system prompt)."""
    if _KB_HDR not in system:
        return ""
    after = system.split(_KB_HDR, 1)[1].lstrip()
    if after.startswith("\n"):
        after = after[1:]
    end_markers = (
        "\n\n" + _WEB_INJECT_HEAD,
        "\n" + _WEB_INJECT_HEAD,
        "\n\nReferências consultadas",
        "\nReferências consultadas",
        "\n\nMetadados internos",
        "\nMetadados internos",
        "\n\nMemória de conversas anteriores",
        "\nMemória de conversas anteriores",
    )
    end = len(after)
    for m in end_markers:
        i = after.find(m)
        if i != -1:
            end = min(end, i)
    return after[:end].strip()[:6000]


def _extract_web_and_refs(system: str) -> tuple[str, str]:
    """Extrai apenas o bloco «Contexto da web» injetado pelo backend — não frases que citam essas palavras na identidade."""
    web = ""
    refs = ""

    if _WEB_INJECT_HEAD not in system:
        return web, _extract_refs_only(system)

    anchor = system.find(_WEB_INJECT_HEAD)
    start_content = system.find(_WEB_CONTENT_AFTER, anchor)
    if start_content == -1:
        return web, _extract_refs_only(system)
    start_content += len(_WEB_CONTENT_AFTER)
    end = len(system)
    for stop in (
        "\n\n" + _REF_HDR.strip(),
        "\n" + _REF_HDR.strip(),
        "\n\nMetadados internos",
        "\nMetadados internos",
        "\n\nMemória de conversas anteriores:",
        "\nMemória de conversas anteriores:",
    ):
        j = system.find(stop, start_content)
        if j != -1:
            end = min(end, j)
    web = system[start_content:end].strip()

    ref_block = ""
    if _REF_HDR in system:
        r0 = system.find(_REF_HDR) + len(_REF_HDR)
        r1 = len(system)
        for stop in ("\n\nMemória de conversas anteriores:", "\nMemória de conversas anteriores:"):
            j = system.find(stop, r0)
            if j != -1:
                r1 = min(r1, j)
        ref_block = system[r0:r1].strip()
        for stop in ("Metadados internos",):
            if stop in ref_block:
                ref_block = ref_block.split(stop, 1)[0].strip()
    refs = ref_block

    return web, refs


def _extract_refs_only(system: str) -> str:
    if _REF_HDR not in system:
        return ""
    r0 = system.find(_REF_HDR) + len(_REF_HDR)
    r1 = len(system)
    for stop in (
        "\n\nMetadados internos",
        "\nMetadados internos",
        "\n\nMemória de conversas anteriores:",
        "\nMemória de conversas anteriores:",
    ):
        j = system.find(stop, r0)
        if j != -1:
            r1 = min(r1, j)
    return system[r0:r1].strip()


def _score_sentences(text: str, query: str) -> list[tuple[float, str]]:
    q_words = {w for w in re.findall(r"\w{3,}", (query or "").lower()) if len(w) > 2}
    if not q_words:
        q_words = {w for w in re.findall(r"\w+", (query or "").lower()) if w}
    parts = re.split(r"(?<=[\.\!\?])\s+", (text or "").strip())
    out: list[tuple[float, str]] = []
    for s in parts:
        s = s.strip()
        if len(s) < 25:
            continue
        sw = {w for w in re.findall(r"\w+", s.lower()) if len(w) > 2}
        inter = len(q_words & sw)
        score = inter / (len(q_words) + 1.0) + min(1.0, len(s) / 1200.0) * 0.15
        out.append((score, s))
    out.sort(key=lambda x: -x[0])
    return out


def _dedupe_sentences(sents: list[str]) -> list[str]:
    out: list[str] = []
    for s in sents:
        s = s.strip()
        if len(s) < 20:
            continue
        dup = False
        for prev in out:
            wa, wb = set(s.lower().split()), set(prev.lower().split())
            inter = len(wa & wb)
            if inter > 5 and inter / max(len(wa), 1) > 0.72:
                dup = True
                break
        if not dup:
            out.append(s)
    return out


def _compose_from_sources(user_q: str, web: str, kb: str, refs: str, *, deep: bool = False) -> str:
    """Composição a partir de fontes: síntese em duas camadas (resposta directa + detalhes), como um assistente."""
    scored = _score_sentences(web, user_q)
    top_n = 24 if deep else 14
    rest_cap = 14 if deep else 8
    kb_cap = 4000 if deep else 2000
    web_fallback = 5500 if deep else 3500
    refs_cap = 6000 if deep else 4000
    out_cap = 18000 if deep else 12000

    body_sents = _dedupe_sentences([s for _, s in scored[:top_n]])
    if not body_sents and web:
        body_sents = [web[:web_fallback]]

    chunks: list[str] = []
    if kb:
        chunks.append("**Da base de conhecimento do sistema:**\n" + kb[:kb_cap])

    if body_sents:
        lead = body_sents[0]
        rest = _dedupe_sentences(body_sents[1:rest_cap])
        chunks.append("**Resposta (síntese):**\n" + lead)
        if rest:
            chunks.append("**Detalhes a partir das fontes:**\n\n" + "\n\n".join(rest))

    elif not kb:
        return ""

    tail = []
    if refs:
        tail.append("**Referências (títulos/URLs indexados):**\n" + refs[:refs_cap])
    out = "\n\n".join(chunks + tail).strip()
    if len(out) > out_cap:
        out = out[:out_cap] + "\n\n*(Resposta truncada — peça mais detalhes numa pergunta de seguimento.)*"
    return out


def _extractive_summary(text: str, max_sentences: int = 3) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", raw)
    chunk = parts[:max_sentences]
    return " ".join(s for s in chunk if s).strip()


def _detect_intent(text: str) -> str:
    t = text.strip()
    if not t:
        return "vazio"
    for name, pats in _INTENT_PATTERNS:
        for p in pats:
            if p.search(t):
                return name
    return "geral"


def _syntexa_pipeline_footer() -> str:
    """Nota curta após síntese com fontes — opcionalmente pode ser desativada no futuro."""
    return "\n\n---\n*Fontes agregadas pelo backend; pode pedir mais detalhe ou uma nova busca.*"


def _reply_for_intent(intent: str, user_text: str) -> str:
    """
    Respostas baseadas na identidade Syntexa para intents básicos.
    Quando a Foundation Model não está disponível mas o usuário faz
    perguntas de identidade, saudação ou ajuda, a Syntexa responde
    a partir da sua definição interna — sem depender de APIs externas.
    """
    if intent == "saudacao":
        return (
            "Olá! Sou a **Syntexa**, assistente de inteligência artificial brasileira "
            "desenvolvida para ajudar em diversas áreas: programação, engenharia, "
            "ciência, jurídico, agronegócio e muito mais.\n\n"
            "Como posso ajudar você hoje?"
        )
    if intent == "ajuda":
        return (
            "Sou a **Syntexa**, uma IA multimodal brasileira. Posso ajudar com:\n\n"
            "- **Código**: gerar, revisar e otimizar em qualquer linguagem\n"
            "- **Engenharia**: cálculos técnicos, viabilidade, projetos\n"
            "- **Ciência**: análise de dados, pesquisa, matemática\n"
            "- **Jurídico**: análise técnica de legislação brasileira\n"
            "- **Agronegócio**: produtividade, análise de solo, planejamento\n"
            "- **Texto**: redação, revisão, estratégia, relatórios\n\n"
            "Basta perguntar — estou pronta para ajudar."
        )
    if intent == "vazio":
        return "Por favor, envie uma mensagem para que eu possa ajudar."
    # Para outros intents (código, matemática, geral) que precisam de contexto real
    return (
        "Sou a **Syntexa**, IA brasileira soberana. Estou processando sua solicitação "
        "com base nos meus recursos internos.\n\n"
        "Para respostas mais completas sobre temas factuais e atualizados, "
        "tente reformular sua pergunta com mais contexto — isso me permite "
        "buscar fontes relevantes e sintetizar uma resposta mais precisa."
    )


def generate_reply(messages: list[dict[str, Any]], **_kwargs: Any) -> str:
    """
    Ordem (acrescenta sem apagar):
    1) Foundation Model Syntexa (decoder-only Transformer próprio) se disponível.
    2) Runtime existente (checkpoints torch legados).
    3) Se o sistema trouxe KB e/ou trechos da web — sintetizar.
    4) Neural Engine de terceiros (20B+ params, 4-bit).
    5) Caso contrário — resposta por intents / sumarização interna.
    """
    # 1) Foundation Model Soberana (nova arquitetura)
    if is_foundation_available():
        try:
            return foundation_generate(messages, max_new_tokens=512, temperature=0.7, top_p=0.9)
        except Exception as e:
            logger.warning("[hybrid_engine] Foundation Model falhou: %s", e)

    # 2) Runtime legado (checkpoints antigos)
    runtime_reply = maybe_runtime_reply(messages)
    if runtime_reply:
        return runtime_reply

    active = get_registry().get_active()
    strict_no_fallback = bool(getattr(settings, "own_model_strict_no_fallback", False))
    is_prod = str(getattr(settings, "environment", "") or "").lower() in {"prod", "production"}
    if active and str(active.stage or "").lower() != "native_hybrid" and (strict_no_fallback or is_prod):
        raise RuntimeError(
            f"IA própria ativa ('{active.name}') sem runtime pronto; fallback bloqueado em modo estrito."
        )

    system = _gather_system_text(messages)
    user_text = _last_user_text(messages)
    intent = _detect_intent(user_text)

    if system:
        web, refs = _extract_web_and_refs(system)
        kb = _extract_kb_block(system)
        deep = bool(_DEEP_USER_TRIGGERS.search(user_text))
        composed = _compose_from_sources(user_text, web, kb, refs, deep=deep)
        if composed:
            return composed + _syntexa_pipeline_footer()

    # Fallback: resposta baseada na identidade Syntexa para intents básicos
    return _reply_for_intent(intent, user_text)


def generate_reply_stream(messages: list[dict[str, Any]], **_kwargs: Any) -> Iterator[str]:
    # 1) Foundation Model Soberana (streaming real token-by-token)
    if is_foundation_available():
        try:
            yield from foundation_generate_stream(messages, max_new_tokens=512, temperature=0.7, top_p=0.9)
            return
        except Exception as e:
            logger.warning("[hybrid_engine] Foundation Model stream falhou: %s", e)

    # 2) Runtime legado
    rt = maybe_runtime_reply_stream(messages)
    if rt is not None:
        yield from rt
        return

    active = get_registry().get_active()
    strict_no_fallback = bool(getattr(settings, "own_model_strict_no_fallback", False))
    is_prod = str(getattr(settings, "environment", "") or "").lower() in {"prod", "production"}
    if active and str(active.stage or "").lower() != "native_hybrid" and (strict_no_fallback or is_prod):
        raise RuntimeError(
            f"IA própria ativa ('{active.name}') sem runtime pronto; fallback bloqueado em modo estrito."
        )

    # 3) Síntese a partir de web/KB injetados no system prompt (mesmo caminho do generate_reply)
    system = _gather_system_text(messages)
    user_text = _last_user_text(messages)
    intent = _detect_intent(user_text)

    if system:
        web, refs = _extract_web_and_refs(system)
        kb = _extract_kb_block(system)
        deep = bool(_DEEP_USER_TRIGGERS.search(user_text))
        composed = _compose_from_sources(user_text, web, kb, refs, deep=deep)
        if composed:
            full = composed + _syntexa_pipeline_footer()
            chunk_size = 48
            for i in range(0, len(full), chunk_size):
                yield full[i : i + chunk_size]
            return

    # 4) Fallback: resposta baseada na identidade Syntexa
    fallback = _reply_for_intent(intent, user_text)
    chunk_size = 48
    for i in range(0, len(fallback), chunk_size):
        yield fallback[i : i + chunk_size]


def native_embed(texts: list[str], dim: int = 384) -> list[list[float]]:
    """
    Embeddings para RAG/memória — 100% local via SyntexaEmbeddings.
    Sem fallback para APIs externas (Ollama, OpenAI, etc.).
    """
    from vereda_ai.syntexa_core.memory.embeddings import SyntexaEmbeddings
    if not texts:
        return []
    emb = SyntexaEmbeddings(dim=dim)
    return emb.embed(texts)
