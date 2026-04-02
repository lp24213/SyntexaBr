import re
from typing import Any, Dict, List

import numpy as np
from PIL import Image
from fastapi import UploadFile
from sympy import SympifyError, sympify


def evaluate_math_expression(expr: str) -> Dict[str, Any]:
    try:
        sym_expr = sympify(expr)
        result = sym_expr.evalf()
        return {
            "ok": True,
            "expression": str(sym_expr),
            "result": float(result),
        }
    except (SympifyError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "error": f"Expressão inválida ou não suportada: {exc}",
        }


# Caracteres permitidos em expressão matemática (sympy)
_MATH_CHARS = set("0123456789+-*/().eE \t^,_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_MATH_WORDS = {"pi", "e", "sqrt", "sin", "cos", "tan", "log", "factorial"}


def _looks_like_math(s: str) -> bool:
    s = s.strip()
    if len(s) < 2:
        return False
    if not all(c in _MATH_CHARS for c in s):
        return False
    words = re.findall(r"[A-Za-z_]+", s)
    if any(w.lower() not in _MATH_WORDS for w in words):
        return False
    # Exige dígitos, operador matemático ou função reconhecida.
    has_digit = bool(re.search(r"\d", s))
    has_operator = any(op in s for op in ("+", "-", "*", "/", "**", "(", ")"))
    has_math_word = any(w.lower() in _MATH_WORDS for w in words)
    return has_digit and (has_operator or has_math_word or len(words) == 0)


def try_math_reply(content: str) -> tuple[str | None, bool]:
    """
    Se a mensagem for só conta ou 'quanto é X' / 'calcule X', avalia com sympy.
    Retorna (reply_text, True) se tratou; (None, False) caso contrário.
    """
    content = content.strip()
    if not content:
        return None, False

    expr = content
    lower = content.lower().strip()

    # Pergunta direta sobre a constante π (evita resposta prolixa só com prompt de sistema)
    if re.match(
        r"^(qual\s+(é|e)\s+)?(o\s+)?(valor\s+(de\s+)?(π|pi)|quanto\s+vale\s+(π|pi))[\?\.\s!]*$",
        lower,
    ) or re.match(r"^(o\s+)?que\s+(é|e)\s+(π|pi)\??[\s!]*$", lower):
        return (
            "π (pi) é a razão entre o comprimento de uma circunferência e seu diâmetro. "
            "Valor aproximado: 3,1415926535… (irracional).",
            True,
        )

    # Linguagem natural comum em PT-BR -> expressão sympy
    sqrt_match = re.match(
        r"^(qual\s+e\s+a\s+)?raiz\s+quadrada\s+de\s+(.+?)[\?\.\,\;\!\s]*$",
        lower,
        flags=re.IGNORECASE,
    )
    if sqrt_match:
        raw = sqrt_match.group(2).strip()
        raw = raw.replace(",", ".")
        result = evaluate_math_expression(f"sqrt({raw})")
        if result.get("ok"):
            return (f"Resultado: raiz quadrada de {raw} = {result['result']}.", True)
        return f"Não consegui avaliar essa expressão: {result.get('error')}", True

    # Potência em linguagem natural: "2 elevado a 10"
    pow_match = re.match(
        r"^(.+?)\s+elevado\s+a\s+(.+?)[\?\.\,\;\!\s]*$",
        lower,
        flags=re.IGNORECASE,
    )
    if pow_match:
        base = pow_match.group(1).strip().replace(",", ".")
        expo = pow_match.group(2).strip().replace(",", ".")
        result = evaluate_math_expression(f"({base})**({expo})")
        if result.get("ok"):
            return (
                f"Resultado: {base} elevado a {expo} = {result['result']}.",
                True,
            )
        return f"Não consegui avaliar essa expressão: {result.get('error')}", True

    # "fatorial de 7"
    fact_match = re.match(
        r"^fatorial\s+de\s+(.+?)[\?\.\,\;\!\s]*$",
        lower,
        flags=re.IGNORECASE,
    )
    if fact_match:
        n = fact_match.group(1).strip().replace(",", ".")
        result = evaluate_math_expression(f"factorial({n})")
        if result.get("ok"):
            return (f"Resultado: fatorial de {n} = {result['result']}.", True)
        return f"Não consegui avaliar essa expressão: {result.get('error')}", True

    for prefix in ("quanto é", "quanto e", "calcule", "calcular", "quanto dá", "quanto da"):
        if lower.startswith(prefix):
            expr = content[len(prefix) :].strip().rstrip("?.,;")
            break

    # Normalizações simples para SymPy (pt-BR -> função/operação)
    expr = (
        expr.replace(",", ".")
        .replace("^", "**")
    )
    expr = re.sub(r"\bsen\(", "sin(", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\btg\(", "tan(", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bln\(", "log(", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\braiz\s+quadrada\s+de\s+([0-9\.\(\)\+\-\*\/]+)", r"sqrt(\1)", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bfatorial\s+de\s+([0-9\.\(\)\+\-\*\/]+)", r"factorial(\1)", expr, flags=re.IGNORECASE)

    expr = expr.strip()
    if not _looks_like_math(expr):
        return None, False

    result = evaluate_math_expression(expr)
    if result.get("ok"):
        return (
            f"Resultado: {result['expression']} = {result['result']}.",
            True,
        )
    return f"Não consegui avaliar essa expressão: {result.get('error')}", True


def analyze_image_basic(file: UploadFile) -> Dict[str, Any]:
    image = Image.open(file.file)
    image = image.convert("RGB")
    width, height = image.size
    arr = np.array(image)
    mean_color = arr.mean(axis=(0, 1)).tolist()

    return {
        "ok": True,
        "filename": file.filename,
        "format": image.format,
        "size": {"width": width, "height": height},
        "mean_rgb": {
            "r": round(mean_color[0], 2),
            "g": round(mean_color[1], 2),
            "b": round(mean_color[2], 2),
        },
        "description": "Análise básica da imagem (resolução e cor média).",
    }

