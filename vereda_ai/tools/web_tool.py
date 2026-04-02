# -*- coding: utf-8 -*-
"""Ferramenta de consulta HTTP. Opcional; offline retorna erro."""
from typing import Any, Dict

from vereda_ai.tools.base_tool import BaseTool

try:
    import urllib.request
    import json
    _URLLIB_AVAILABLE = True
except ImportError:
    _URLLIB_AVAILABLE = False


class WebTool(BaseTool):
    name = "web"

    def available(self) -> bool:
        return _URLLIB_AVAILABLE

    def run(self, url: str, method: str = "GET", **kwargs: Any) -> Dict[str, Any]:
        if not _URLLIB_AVAILABLE:
            return {"ok": False, "error": "Módulo urllib indisponível."}
        url = (url or "").strip()
        if not url.startswith(("http://", "https://")):
            return {"ok": False, "error": "URL deve ser http(s)://"}
        try:
            req = urllib.request.Request(url, method=method.upper(), headers={"User-Agent": "SyntexaBR/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = body[:2000]
            return {"ok": True, "status": resp.status, "body": body}
        except Exception as e:
            return {"ok": False, "error": str(e)}
