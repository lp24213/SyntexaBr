from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class QueryProfile:
    domains: list[str]
    asks_files: bool
    asks_multimodal: bool
    asks_advanced_math: bool
    asks_extreme_math: bool
    asks_code: bool


def analyze_query_profile(text: str) -> QueryProfile:
    t = (text or "").strip().lower()
    domains: list[str] = []

    checks = [
        ("programacao", r"\b(programa[cç][aã]o|python|javascript|api|backend|frontend|debug)\b"),
        ("engenharia", r"\b(engenharia|torque|pot[êe]ncia|cad|mec[aâ]nica|estrutural)\b"),
        ("matematica", r"\b(matem[aá]tica|equa[cç][aã]o|integral|derivada|otimiza[cç][aã]o|álgebra|algebra)\b"),
        ("fisica", r"\b(f[ií]sica|qu[aâ]ntica|relatividade|termodin[aâ]mica|mec[aâ]nica qu[aâ]ntica)\b"),
        ("quimica", r"\b(qu[ií]mica|estequiometria|liga[cç][aã]o|rea[cç][aã]o|mol)\b"),
        ("biologia", r"\b(biologia|gen[eé]tica|bioqu[ií]mica|microbiologia|ecologia|fisiologia)\b"),
        ("politica", r"\b(pol[ií]tica|geopol[ií]tica|governo|elei[cç][aã]o|diplomacia|rela[cç][oõ]es internacionais)\b"),
        ("literatura", r"\b(literatura|romance|poesia|ensaio|narrativa|estilo liter[aá]rio)\b"),
        ("engenharia social", r"\b(engenharia social|phishing|pretexting|vishing|human hacking|manipula[cç][aã]o social)\b"),
        ("ciencia", r"\b(ci[eê]ncia|cient[ií]fico|paper|doi|revis[aã]o sistem[aá]tica)\b"),
        ("tecnologia", r"\b(tecnologia|ia|intelig[eê]ncia artificial|llm|infraestrutura)\b"),
    ]
    for name, rx in checks:
        if re.search(rx, t, re.I):
            domains.append(name)

    asks_files = bool(
        re.search(r"\b(pdf|excel|xlsx|csv|word|docx|planilha|arquivo|ficheiro|documento)\b", t, re.I)
    )
    asks_multimodal = bool(
        re.search(r"\b(imagem|imagens|v[ií]deo|videos?|[áa]udio|tts|stt|multimodal)\b", t, re.I)
    )
    asks_advanced_math = bool(
        re.search(r"\b(equa[cç][aã]o diferencial|tensor|autovalor|integral de linha|schr[öo]dinger|lagrang)\b", t, re.I)
    )
    asks_extreme_math = bool(
        re.search(
            r"\b(imposs[ií]vel|n[aã]o resolvido|problema do mil[eê]nio|riemann|p vs np|navier[- ]stokes|yang[- ]mills)\b",
            t,
            re.I,
        )
    )
    asks_code = bool(re.search(r"\b(c[oó]digo|script|fun[cç][aã]o|classe|algoritmo)\b", t, re.I))

    return QueryProfile(
        domains=domains,
        asks_files=asks_files,
        asks_multimodal=asks_multimodal,
        asks_advanced_math=asks_advanced_math,
        asks_extreme_math=asks_extreme_math,
        asks_code=asks_code,
    )


def build_profile_directives(profile: QueryProfile) -> str:
    parts: list[str] = [
        "PERFIL DO PEDIDO (uso interno): adapte formato e profundidade ao tipo de tarefa."
    ]
    if profile.domains:
        parts.append("• Domínios detectados: " + ", ".join(profile.domains) + ".")
    if profile.asks_code:
        parts.append("• Se envolver código, entregue solução executável + passos de validação.")
    if profile.asks_advanced_math:
        parts.append("• Em matemática/física avançada, mostre definição, derivação e resultado final.")
    if "biologia" in profile.domains or "quimica" in profile.domains or "fisica" in profile.domains:
        parts.append(
            "• Em ciências naturais, priorize rigor conceitual, unidades corretas, hipóteses explícitas e limitações do modelo."
        )
    if "politica" in profile.domains or "literatura" in profile.domains:
        parts.append(
            "• Em política/literatura, traga contexto histórico, perspectivas comparadas e distinção clara entre fato e interpretação."
        )
    if "engenharia social" in profile.domains:
        parts.append(
            "• Em engenharia social, enfoque defensivo: prevenção, treino de usuários, simulação ética e controles anti-fraude."
        )
    if profile.asks_extreme_math:
        parts.append(
            "• Em problemas matemáticos em aberto, seja rigoroso: diferencie resultado provado vs aproximação numérica e entregue estratégia computacional reproduzível."
        )
    if profile.asks_files:
        parts.append(
            "• Se pedirem ficheiros (PDF/Excel/Word/CSV), produza conteúdo completo e informe que o download é gerado pelo sistema."
        )
    if profile.asks_multimodal:
        parts.append(
            "• Se pedirem imagem/vídeo/áudio, entregue prompt técnico, parâmetros e workflow de geração/edição."
        )
    if len(parts) == 1:
        parts.append("• Responda em formato directo e útil, com exemplos quando relevante.")
    return "\n".join(parts)
