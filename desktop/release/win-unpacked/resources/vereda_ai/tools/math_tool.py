# -*- coding: utf-8 -*-
"""Ferramenta de matemática com Sympy. Funciona offline."""
from typing import Any, Dict

from vereda_ai.tools.base_tool import BaseTool

try:
    from sympy import SympifyError, sympify
    _SYMPY_AVAILABLE = True
except ImportError:
    _SYMPY_AVAILABLE = False


class MathTool(BaseTool):
    name = "math"

    def available(self) -> bool:
        return _SYMPY_AVAILABLE

    def run(self, expression: str, **kwargs: Any) -> Dict[str, Any]:
        if not _SYMPY_AVAILABLE:
            return {"ok": False, "error": "Sympy não instalado."}
        expr = (expression or "").strip()
        if not expr:
            return {"ok": False, "error": "Expressão vazia."}
        try:
            sym_expr = sympify(expr)
            result = sym_expr.evalf()
            return {"ok": True, "expression": str(sym_expr), "result": float(result)}
        except (SympifyError, TypeError, ValueError) as e:
            return {"ok": False, "error": str(e)}
