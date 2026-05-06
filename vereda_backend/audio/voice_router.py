"""Roteamento de comandos de voz (PT-BR) após STT — alinhado às intenções do chat (imagem, vídeo, áudio, ficheiros)."""
from __future__ import annotations

import re
from typing import Any, Dict, Literal

Intent = Literal[
    "chat",
    "generate_image",
    "generate_video",
    "generate_music",
    "read_aloud",
    "unknown",
]


def _extract_image_prompt(raw: str) -> str:
    s = (raw or "").strip()
    m = re.search(
        r"(?:imagem|foto|ilustra(?:ção|çao)?|desenho)\s+(?:de|com|do|da|que|mostrando)\s+(.+)$",
        s,
        re.I | re.S,
    )
    if m:
        return m.group(1).strip()[:4000]
    m2 = re.search(r"(?:mostra|mostre|quero)\s+(?:uma\s+)?(?:imagem|foto)\s+(?:de|com)?\s*(.+)$", s, re.I | re.S)
    if m2:
        return m2.group(1).strip()[:4000]
    return s[:4000]


def _extract_video_prompt(raw: str) -> str:
    s = (raw or "").strip()
    m = re.search(
        r"(?:vídeo|video|videoclip|anima(?:ção|çao))\s+(?:de|com|sobre)?\s*(.+)$",
        s,
        re.I | re.S,
    )
    if m:
        return m.group(1).strip()[:4000]
    return s[:4000]


def _extract_music_prompt(raw: str) -> str:
    s = (raw or "").strip()
    m = re.search(
        r"(?:música|musica|som|trilha|beat|instrumental)\s+(?:de|com)?\s*(.+)$",
        s,
        re.I | re.S,
    )
    if m:
        return m.group(1).strip()[:4000]
    return s[:4000]


def _wants_image(t: str) -> bool:
    """Pedido explícito de imagem/foto/ilustração (como detectMediaIntent no frontend)."""
    return bool(
        re.search(
            r"\b(crie|criar|gere|gera|desenhe|desenha|faça|faca|fazer|elabore|produza|monte|mostra|mostre|quero)\s+(?:uma\s+)?(imagem|foto|ilustra|desenho)\b",
            t,
        )
        or re.search(r"\bquero\s+(?:uma\s+)?(imagem|foto)\b", t)
        or re.search(r"\b(me\s+)?(faz|faça|faca)\s+(uma\s+)?(imagem|foto)\b", t)
        or re.search(r"\b(imagem|foto)\s+de\s+", t)
        or re.search(r"\bilustra(?:ção|çao)\b", t)
        or re.search(r"\bgere\s+(?:uma\s+)?(imagem|foto)\b", t)
        or re.search(r"\bgera\s+(?:uma\s+)?(imagem|foto)\b", t)
    )


def _wants_video(t: str) -> bool:
    return bool(
        re.search(
            r"\b(crie|criar|gere|gera|faça|faca|fazer|mostra|mostre)\s+(?:um\s+)?(vídeo|video|videoclip|clip)\b",
            t,
        )
        or re.search(r"\b(vídeo|video)\s+(de|com|sobre)\s+", t)
    )


def _wants_music(t: str) -> bool:
    """Áudio/música instrumental — não confundir com pedido de ‘texto em voz’."""
    if re.search(r"\b(voz|falar|ler|narra|texto\s+em\s+voz)\b", t):
        return False
    return bool(
        re.search(
            r"\b(crie|criar|gere|gera|faça|faca)\s+(?:um\s+)?(áudio|audio|som|música|musica|trilha|beat)\b",
            t,
        )
        or re.search(r"\bmúsica\s+instrumental\b", t)
    )


def route_voice_intent(transcript: str) -> Dict[str, Any]:
    raw = (transcript or "").strip()
    t = raw.lower()
    if not t:
        return {"intent": "unknown", "confidence": 0.0, "payload": {}}

    if _wants_image(t):
        prompt = _extract_image_prompt(raw)
        return {"intent": "generate_image", "confidence": 0.88, "payload": {"prompt": prompt}}

    if _wants_video(t):
        prompt = _extract_video_prompt(raw)
        return {"intent": "generate_video", "confidence": 0.82, "payload": {"prompt": prompt}}

    if _wants_music(t):
        prompt = _extract_music_prompt(raw)
        return {"intent": "generate_music", "confidence": 0.78, "payload": {"prompt": prompt}}

    if re.search(r"\b(leia|ler|narre|narra)\s+(?:em\s+voz|aloud)?", t) and not _wants_music(t):
        return {"intent": "read_aloud", "confidence": 0.6, "payload": {}}

    return {"intent": "chat", "confidence": 0.55, "payload": {"message": transcript}}
