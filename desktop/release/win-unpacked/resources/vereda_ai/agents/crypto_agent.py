# -*- coding: utf-8 -*-
"""Agente de criptomoedas. Usa CryptoTool para preço."""
from typing import Any, Dict

from vereda_ai.agents.base_agent import BaseAgent
from vereda_ai.tools.crypto_tool import CryptoTool


class CryptoAgent(BaseAgent):
    name = "crypto"

    def __init__(self, llm=None):
        self.tool = CryptoTool()
        self.llm = llm

    def handle(self, prompt: str, context: Dict[str, Any]) -> str:
        prompt = (prompt or "").strip().lower()
        symbol = "BTC"
        if "eth" in prompt or "ethereum" in prompt:
            symbol = "ETH"
        elif "btc" in prompt or "bitcoin" in prompt:
            symbol = "BTC"
        out = self.tool.run(symbol=symbol)
        if out.get("ok"):
            brl = out.get("brl")
            usd = out.get("usd")
            return f"{symbol}: BRL {brl}, USD {usd} (fonte: API pública)."
        if self.llm:
            messages = [
                {"role": "system", "content": "Você explica criptomoedas e mercados. Se a consulta de preço falhou, explique que é necessário internet."},
                {"role": "user", "content": prompt},
            ]
            return self.llm.chat(messages)
        return out.get("error", "Consulta de preço indisponível (offline?).")
