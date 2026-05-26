# -*- coding: utf-8 -*-
"""Ferramenta de preço de criptomoedas. Requer internet; offline retorna mensagem."""
from typing import Any, Dict

from vereda_ai.tools.base_tool import BaseTool

try:
    import urllib.request
    import json
    _URLLIB_AVAILABLE = True
except ImportError:
    _URLLIB_AVAILABLE = False


class CryptoTool(BaseTool):
    name = "crypto"

    def available(self) -> bool:
        return _URLLIB_AVAILABLE

    def run(self, symbol: str = "BTC", **kwargs: Any) -> Dict[str, Any]:
        """
        Obtém preço aproximado (API pública gratuita). Offline: retorna erro amigável.
        symbol: BTC, ETH, etc.
        """
        if not _URLLIB_AVAILABLE:
            return {"ok": False, "error": "Módulo urllib indisponível."}
        symbol = (symbol or "BTC").upper()
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=brl,usd"
            req = urllib.request.Request(url, headers={"User-Agent": "SyntexaBR/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            mapping = {"BTC": "bitcoin", "ETH": "ethereum"}
            id_ = mapping.get(symbol, "bitcoin")
            if id_ not in data:
                return {"ok": False, "error": f"Moeda {symbol} não suportada."}
            return {
                "ok": True,
                "symbol": symbol,
                "brl": data[id_].get("brl"),
                "usd": data[id_].get("usd"),
            }
        except Exception as e:
            return {"ok": False, "error": f"Consulta offline ou falha: {e}"}
