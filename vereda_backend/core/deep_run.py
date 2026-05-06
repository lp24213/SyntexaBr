# -*- coding: utf-8 -*-
"""Detecção de pedidos de resposta profunda (estrutura + mais contexto híbrido)."""
from __future__ import annotations

import re

_DEEP_TRIGGERS = re.compile(
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


def user_requests_deep_answer(text: str) -> bool:
    return bool(_DEEP_TRIGGERS.search(text or ""))
