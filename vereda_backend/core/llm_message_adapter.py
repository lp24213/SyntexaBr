# -*- coding: utf-8 -*-
"""
Adapta mensagens OpenAI-like para o motor interno (só role+texto) ou repassa inteiras ao HTTP.
Permite evoluir para tool-calls / multimodal sem quebrar o núcleo híbrido.
"""
from __future__ import annotations

import json
from typing import Any


def adapt_messages_for_llm_provider(
    messages: list[dict[str, Any]],
    provider_name: str,
) -> list[dict[str, Any]]:
    name = (provider_name or "").strip().lower()
    if name in ("syntexa_native", "future_syntexa", "dummy"):
        return _collapse_for_native_core(messages)
    return messages


def _collapse_for_native_core(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        role = str(m.get("role") or "user").lower()
        content = str(m.get("content") or "")
        if role == "tool":
            content = f"[resultado ferramenta id={m.get('tool_call_id', '')}]\n{content}"
            role = "user"
        if role not in ("system", "user", "assistant"):
            role = "user"
        tc = m.get("tool_calls")
        if tc:
            try:
                snippet = json.dumps(tc, ensure_ascii=False)[:6000]
            except (TypeError, ValueError):
                snippet = str(tc)[:6000]
            if content.strip():
                content = content.rstrip() + "\n\n[tool_calls]\n" + snippet
            else:
                content = "[tool_calls]\n" + snippet
        extra_name = m.get("name")
        if extra_name and role == "user":
            content = f"[{extra_name}]\n{content}"
        out.append({"role": role, "content": content})
    return out
