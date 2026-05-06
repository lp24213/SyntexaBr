"""
Módulo de Educação & Pesquisa — SyntexaBR (Expansão Máxima)

Endpoints públicos (sem auth):
  POST /v1/education/tutor               — tutor por disciplina (nível + idioma)
  POST /v1/education/tutor/stream        — streaming do tutor
  POST /v1/education/compute             — motor de cálculo simbólico/numérico (sympy)
  POST /v1/education/compute/code        — sandbox de execução de código (Python/JS) [AUTH REQUIRED]

Endpoints autenticados (professor/pesquisador):
  POST /v1/education/teacher/chat        — ferramentas avançadas para professores
  POST /v1/education/teacher/chat/stream — streaming para professor
  POST /v1/education/teacher/research    — análise de papers e escrita acadêmica
  GET  /v1/education/teacher/profile     — perfil do professor

Endpoints administrativos (governo):
  GET  /v1/education/gov/stats           — indicadores educacionais nacionais
  POST /v1/education/gov/report          — relatório gerado por IA
  POST /v1/education/gov/predict         — previsões com IA (evasão, desempenho)
  POST /v1/education/gov/policy          — geração de políticas públicas
"""

import hashlib
import json
import logging
import re
import subprocess
import sys
import tempfile
import textwrap
import time
from typing import Any, Dict, Iterator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from fastapi import Request as _Request

from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.core.security import (
    get_current_user,
    get_current_user_optional,
    get_current_admin,
)
from vereda_backend.core.cache_redis import (
    compute_cache_get,
    compute_cache_set,
    edu_public_cache_get,
    edu_public_cache_set,
)
from vereda_backend.core.config import settings
from vereda_backend.core.job_queue import job_queue_enabled, run_gov_report_sync
from vereda_backend.core.rate_limit import RateLimiter, get_client_ip
from vereda_backend.schemas.chat import ChatMessage, ChatRequest
from vereda_backend.services.chat_engine import create_chat_completion, stream_chat_completion

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/education")

# Rate limiters para endpoints públicos de educação
# Tutor: tiers por IP — logados e gov com mais folga (mesmo servidor)
_edu_tutor_anon = RateLimiter(max_calls=60, window_seconds=3600, max_keys=10_000)
_edu_tutor_auth = RateLimiter(max_calls=120, window_seconds=3600, max_keys=15_000)
_edu_tutor_gov = RateLimiter(max_calls=400, window_seconds=3600, max_keys=5_000)
# Cálculo simbólico: 30/hora por IP (operação mais pesada)
_edu_compute_limiter = RateLimiter(max_calls=30, window_seconds=3600, max_keys=5_000)
# Concursos / ciência: 40/hora por IP
_edu_concursos_limiter = RateLimiter(max_calls=40, window_seconds=3600, max_keys=5_000)


def _edu_tutor_rate_check(request: _Request, user: Optional[models.User]) -> None:
    ip = get_client_ip(request)
    detail = "Limite de uso do tutor atingido. Tente mais tarde ou crie uma conta."
    if user:
        plan = (getattr(user, "subscription_plan", "") or "").lower()
        if plan in ("gov", "government") or getattr(user, "is_admin", False):
            _edu_tutor_gov.check(ip, detail=detail)
        else:
            _edu_tutor_auth.check(ip, detail=detail)
    else:
        _edu_tutor_anon.check(ip, detail=detail)


# ============================================================
# Schemas
# ============================================================

class TutorRequest(BaseModel):
    discipline: str = Field(default="geral", max_length=64)
    question: str = Field(..., min_length=1, max_length=4000)
    mode: str = Field(default="chat", max_length=32)
    level: str = Field(default="intermediario", max_length=32)
    language: str = Field(default="pt", max_length=8)
    history: list = Field(default=[], max_length=30)  # máx 30 mensagens no histórico
    feedback: Optional[str] = Field(default=None, max_length=16)


class ComputeRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=2000)
    compute_type: str = Field(default="auto", max_length=32)
    variable: str = Field(default="x", max_length=16)
    extra: Optional[Dict[str, Any]] = None


class CodeSandboxRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=8000)
    language: str = Field(default="python", max_length=16)
    timeout: int = Field(default=10, ge=1, le=30)


class TeacherChatRequest(BaseModel):
    task: str = Field(default="pesquisa", max_length=64)
    content: str = Field(..., min_length=1, max_length=8000)
    context: Optional[str] = Field(default=None, max_length=2000)
    level: str = Field(default="avancado", max_length=32)
    language: str = Field(default="pt", max_length=8)


class ResearchRequest(BaseModel):
    task: str = Field(default="analisar", max_length=64)
    content: str = Field(..., min_length=1, max_length=16000)
    extra: Optional[str] = Field(default=None, max_length=2000)
    language: str = Field(default="pt", max_length=8)


class GovPredictRequest(BaseModel):
    scenario: str = Field(..., max_length=64)
    context: Optional[str] = Field(default=None, max_length=2000)


class GovPolicyRequest(BaseModel):
    challenge: str = Field(..., min_length=1, max_length=2000)
    region: Optional[str] = Field(default=None, max_length=128)
    budget: Optional[str] = Field(default=None, max_length=64)


# ============================================================
# Language map
# ============================================================

LANG_INSTRUCTION = {
    "pt": "Responda em português brasileiro.",
    "en": "Respond in English.",
    "es": "Responde en español.",
    "zh": "请用中文回答。",
}

LANG_LABEL = {
    "pt": "Português",
    "en": "English",
    "es": "Español",
    "zh": "中文",
}

# ============================================================
# Level context suffixes
# ============================================================

LEVEL_CONTEXT = {
    "basico": (
        "Use linguagem simples, exemplos do cotidiano e evite jargões técnicos. "
        "O aluno é do ensino fundamental ou iniciante absoluto."
    ),
    "intermediario": (
        "Use linguagem clara com terminologia técnica básica. "
        "O aluno é do ensino médio ou possui conhecimento introdutório."
    ),
    "avancado": (
        "Use terminologia técnica completa com rigor conceitual. "
        "O aluno é universitário ou possui formação intermediária."
    ),
    "especialista": (
        "Use linguagem científica, fórmulas e referências teóricas. "
        "O leitor é um pesquisador, docente ou especialista na área."
    ),
}

# ============================================================
# Discipline system prompts
# ============================================================

DISCIPLINE_SYSTEM = {
    # ── Ciências Exatas ──────────────────────────────────────────────────
    "matematica": (
        "Você é um tutor de Matemática de altíssimo nível especializado em álgebra, cálculo, "
        "álgebra linear, estatística, equações diferenciais e otimização. "
        "Sempre mostre equações passo a passo, indique a fórmula usada e interprete o resultado. "
        "Para exercícios, resolva detalhadamente e forneça gabarito."
    ),
    "fisica": (
        "Você é um tutor de Física cobrindo mecânica clássica, termodinâmica, eletromagnetismo, "
        "óptica, ondas e física moderna (relatividade, quântica, partículas). "
        "Apresente as leis e equações relevantes, resolva com unidades SI e interprete fisicamente."
    ),
    "quimica": (
        "Você é um tutor de Química especializado em química geral, orgânica, inorgânica, "
        "cinética, equilíbrio, eletroquímica e espectroscopia. "
        "Balance equações passo a passo, calcule estequiometria e explique mecanismos de reação."
    ),
    # ── Tecnologia & Computação ──────────────────────────────────────────
    "programacao": (
        "Você é um tutor de Programação e Ciência da Computação. Domina Python, JavaScript, "
        "C, C++, Rust, algoritmos, estruturas de dados, complexidade computacional, POO, bancos de "
        "dados, redes e sistemas operacionais. Forneça código funcional comentado, explique a lógica "
        "passo a passo e indique complexidade Big-O."
    ),
    "engenharia": (
        "Você é um tutor de Engenharia cobrindo cálculo aplicado, resistência dos materiais, "
        "circuitos elétricos, análise estrutural, termodinâmica de máquinas, sinais e controle. "
        "Resolva com unidades, diagramas e verificação dimensional."
    ),
    "inteligencia_artificial": (
        "Você é um especialista em Inteligência Artificial, Machine Learning e Deep Learning. "
        "Domina regressão, classificação, redes neurais (CNN, RNN, Transformers), RL, NLP, visão "
        "computacional, ética em IA e aplicações práticas. "
        "Explique conceitos matemáticos subjacentes e forneça exemplos de código PyTorch/TensorFlow/sklearn."
    ),
    "seguranca_digital": (
        "Você é um especialista em Segurança da Informação, Cibersegurança e Privacidade Digital. "
        "Cobre: criptografia (simétrica, assimétrica, hashing), segurança de redes, pentest ético, "
        "OWASP Top 10, análise de malware, privacidade (LGPD, GDPR), segurança em cloud, "
        "e boas práticas de desenvolvimento seguro (DevSecOps). "
        "Foque em educação e defesa — nunca forneça instruções para ataques reais."
    ),
    "computacao_quantica": (
        "Você é um especialista em Computação Quântica. "
        "Explica qubits, superposição, entrelaçamento, portas quânticas, algoritmos de Shor e Grover, "
        "circuitos quânticos, decoerência, correção de erros quânticos e plataformas (Qiskit, Cirq). "
        "Use analogias claras para conceitos abstratos."
    ),
    # ── Ciências da Vida ─────────────────────────────────────────────────
    "biologia": (
        "Você é um tutor de Biologia especializado em biologia celular, genética, evolução, "
        "ecologia, fisiologia humana e biologia molecular. "
        "Explique com exemplos concretos e interações sistêmicas."
    ),
    "bioinformatica": (
        "Você é um especialista em Bioinformática e Biologia Computacional. "
        "Cobre: sequenciamento de DNA/RNA, análise de genomas, alinhamento de sequências (BLAST, "
        "Needleman-Wunsch), estrutura de proteínas, redes metabólicas, transcriptômica e ferramentas "
        "como BioPython, R/Bioconductor e bancos de dados (GenBank, UniProt, PDB). "
        "Conecte biologia com computação de forma rigorosa."
    ),
    "neurociencias": (
        "Você é um especialista em Neurociências cobrindo neuroanatomia, neurofisiologia, "
        "neuropsicologia, neuroimagem (fMRI, EEG), plasticidade sináptica, neurobiologia do aprendizado, "
        "transtornos neurológicos e psiquiátricos, e interfaces cérebro-máquina. "
        "Use linguagem precisa e evidências de pesquisas recentes."
    ),
    "saude": (
        "Você é um tutor de Ciências da Saúde cobrindo anatomia, fisiologia, farmacologia básica, "
        "epidemiologia, saúde pública e primeiros socorros. "
        "Responda com rigor científico e lembre que consultas médicas individuais requerem profissional. "
        "Não forneça diagnósticos — forneça conhecimento educacional."
    ),
    # ── Ciências da Terra & Universo ─────────────────────────────────────
    "astronomia": (
        "Você é um astrônomo e cosmólogo especialista em astrofísica, mecânica celeste, "
        "formação estelar, galáxias, buracos negros, cosmologia (Big Bang, inflação, energia escura), "
        "instrumentação (telescópios, radioastronomia) e exploração espacial. "
        "Conecte fenômenos cósmicos com física fundamental e use escala de grandeza."
    ),
    "ciencias_ambientais": (
        "Você é um especialista em Ciências Ambientais, Ecologia e Sustentabilidade. "
        "Cobre mudanças climáticas (IPCC), ciclos biogeoquímicos, biodiversidade, poluição, "
        "energias renováveis, gestão de resíduos, legislação ambiental brasileira e internacional, "
        "e soluções baseadas na natureza. Use dados científicos atualizados."
    ),
    # ── Ciências Humanas & Sociais ────────────────────────────────────────
    "historia": (
        "Você é um tutor de História cobrindo história mundial, brasileira e contemporânea. "
        "Contextualize eventos, causas, consequências e conecte com o presente."
    ),
    "economia": (
        "Você é um tutor de Economia e Finanças cobrindo micro e macroeconomia, econometria, "
        "mercados financeiros, finanças pessoais, política monetária e fiscal, comércio internacional "
        "e economia comportamental. Sempre use dados, gráficos em texto e exemplos brasileiros."
    ),
    "direito": (
        "Você é um tutor de Direito especializado em Direito Constitucional, Civil, Penal, Trabalhista, "
        "Administrativo, Digital (LGPD, Marco Civil) e Direitos Humanos. "
        "Explique institutos jurídicos, cite legislação e jurisprudência. "
        "Não forneça consultoria jurídica individualizada — forneça educação jurídica."
    ),
    # ── Geral ─────────────────────────────────────────────────────────────
    "geral": (
        "Você é um tutor educacional completo, especialista em todas as disciplinas do ensino "
        "fundamental ao pós-doutorado. Adapte profundidade e linguagem ao contexto do aluno."
    ),
}

MODE_SUFFIX = {
    "chat": "",
    "exercicio": (
        "\n\nAo final da resposta, gere EXATAMENTE 3 exercícios progressivos (fácil, médio, difícil) "
        "com gabarito completo e justificativa."
    ),
    "simulado": (
        "\n\nGere uma questão completa no estilo ENEM/Vestibular: contexto introdutório, "
        "enunciado claro, 5 alternativas (A-E) com somente uma correta. "
        "Após as alternativas, explique o gabarito detalhadamente."
    ),
    "calculo": (
        "\n\nModo Cálculo Exato: resolva com todo rigor matemático, mostrando cada etapa algébrica, "
        "as fórmulas aplicadas, e finalize com a interpretação do resultado. "
        "Se houver gráfico relevante, descreva-o em texto."
    ),
    "pesquisa": (
        "\n\nModo Pesquisa: forneça uma análise aprofundada em nível de publicação científica. "
        "Inclua: fundamentação teórica, estado da arte, metodologias relevantes e referências conceituais."
    ),
}

TEACHER_TASKS = {
    "correcao": (
        "Você é um especialista em avaliação pedagógica e psicometria. "
        "Corrija a resposta do aluno com precisão: pontue acertos (verde), erros conceituais (vermelho), "
        "lacunas (amarelo), atribua nota de 0 a 10 com justificativa e sugira material de revisão."
    ),
    "prova": (
        "Você é um especialista em elaboração de instrumentos de avaliação. "
        "Crie avaliações balanceadas com taxonomia de Bloom: questões de memória, compreensão, "
        "aplicação, análise e criação. Inclua gabarito e rubrica de correção."
    ),
    "material": (
        "Você é um especialista em design instrucional e produção de material didático. "
        "Crie materiais com objetivos de aprendizagem claros, sequência pedagógica, exemplos, "
        "atividades e referências bibliográficas."
    ),
    "turma": (
        "Você é um especialista em gestão educacional e planejamento pedagógico. "
        "Auxilie com cronogramas, sequências didáticas, registros de turma e análise de desempenho coletivo."
    ),
    "pesquisa": (
        "Você é um assistente de pesquisa científica de alto nível. "
        "Auxilie com: revisão de literatura, formulação de hipóteses, design experimental, "
        "análise estatística, escrita acadêmica e resposta a pareceristas."
    ),
    "plano_aula": (
        "Você é um especialista em planejamento didático. "
        "Crie planos de aula completos com: objetivos SMART, justificativa curricular (BNCC), "
        "sequência didática, recursos necessários, avaliação formativa e referências."
    ),
}

RESEARCH_TASKS = {
    "analisar": (
        "Você é um revisor científico experiente (peer reviewer). "
        "Analise o texto fornecido extraindo: (1) problema de pesquisa, (2) hipóteses, "
        "(3) metodologia, (4) principais resultados, (5) limitações, (6) contribuições originais. "
        "Formate como relatório estruturado."
    ),
    "resumir": (
        "Você é especialista em síntese acadêmica. "
        "Produza um resumo estruturado do texto em: Abstract (150 palavras), "
        "pontos principais (5 itens), e implicações práticas."
    ),
    "hipoteses": (
        "Você é um cientista sênior especializado em formulação de hipóteses. "
        "Com base no contexto fornecido, gere 5 hipóteses falsificáveis e testáveis, "
        "classificadas por viabilidade e impacto potencial."
    ),
    "experimentos": (
        "Você é um metodologista experimental. "
        "Proponha 3 designs experimentais rigorosos para testar as hipóteses, "
        "incluindo: variáveis (IV, DV, CV), amostragem, métricas, análise estatística e limitações."
    ),
    "escrever": (
        "Você é um escritor acadêmico de alto nível. "
        "Produza texto acadêmico rigoroso, bem estruturado, com argumentação sólida, "
        "coesão e coerência textual, adequado para publicação científica."
    ),
    "revisar": (
        "Você é um revisor técnico e linguístico de textos acadêmicos. "
        "Revise o texto fornecido: corrija erros, melhore clareza, fluidez, precisão técnica "
        "e adequação ao registro acadêmico. Explique cada alteração."
    ),
    "abnt": (
        "Você é especialista em normas ABNT para trabalhos acadêmicos brasileiros. "
        "Formate ou corrija o texto conforme NBR 6023, NBR 6024, NBR 10520, NBR 14724. "
        "Forneça o texto formatado + lista de correções aplicadas."
    ),
    "apa": (
        "Você é especialista em normas APA 7ª edição. "
        "Formate ou corrija o texto conforme APA 7th edition guidelines. "
        "Forneça o texto formatado + lista de correções aplicadas."
    ),
}

# ============================================================
# SymPy computation engine
# ============================================================

def _sympy_compute(expression: str, compute_type: str, variable: str = "x", extra: Optional[dict] = None) -> dict:
    """
    Motor de cálculo simbólico usando SymPy.
    Retorna dict com: result, steps, latex, interpretation, error.
    """
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication_application,
        )

        transformations = standard_transformations + (implicit_multiplication_application,)
        var = sp.Symbol(variable)
        local_dict = {variable: var, "e": sp.E, "pi": sp.pi, "oo": sp.oo, "inf": sp.oo}

        # Auto-detect type
        ct = compute_type.lower()
        expr_str = expression.strip()

        if ct == "auto":
            if "d/d" in expr_str.lower() or "derivad" in expr_str.lower():
                ct = "derivada"
            elif "∫" in expr_str or "integral" in expr_str.lower():
                ct = "integral"
            elif "lim" in expr_str.lower() or "limite" in expr_str.lower():
                ct = "limite"
            elif "=" in expr_str and not any(op in expr_str for op in ["==", "<=", ">="]):
                ct = "equacao"
            elif "[" in expr_str or "matriz" in expr_str.lower():
                ct = "matriz"
            elif any(k in expr_str.lower() for k in ["mean", "std", "var", "media", "desvio"]):
                ct = "estatistica"
            else:
                ct = "expressao"

        result_val = None
        steps = []
        interpretation = ""
        latex_result = ""

        if ct == "derivada":
            clean = re.sub(r"d/d[a-z]|derivad[ao] de|derivative of", "", expr_str, flags=re.I).strip()
            expr = parse_expr(clean, local_dict=local_dict, transformations=transformations)
            steps.append(f"Expressão: f({variable}) = {expr}")
            result_val = sp.diff(expr, var)
            steps.append(f"Derivada: f'({variable}) = {result_val}")
            simplified = sp.simplify(result_val)
            if simplified != result_val:
                steps.append(f"Simplificado: {simplified}")
                result_val = simplified
            latex_result = sp.latex(result_val)
            interpretation = f"A derivada representa a taxa de variação instantânea de f em relação a {variable}."

        elif ct == "integral":
            clean = re.sub(r"∫|integral de|integral of", "", expr_str, flags=re.I).strip()
            clean = re.sub(r"d[a-z]$", "", clean).strip()
            expr = parse_expr(clean, local_dict=local_dict, transformations=transformations)
            steps.append(f"Integrando: ∫ {expr} d{variable}")
            result_val = sp.integrate(expr, var)
            steps.append(f"Resultado: {result_val} + C")
            latex_result = sp.latex(result_val) + " + C"
            interpretation = "A integral indefinida representa a antiderivada (família de funções primitivas)."

        elif ct == "limite":
            clean = re.sub(r"lim(ite)?(\s+de)?", "", expr_str, flags=re.I).strip()
            point_match = re.search(r"quando\s+[a-z]\s*[→->]+\s*([^\s,]+)", clean, re.I)
            point = sp.oo
            if point_match:
                pt_str = point_match.group(1).replace("inf", "oo").replace("∞", "oo")
                try:
                    point = parse_expr(pt_str, local_dict=local_dict)
                except Exception:
                    pass
                clean = re.sub(r"quando.*", "", clean, flags=re.I).strip()
            expr = parse_expr(clean, local_dict=local_dict, transformations=transformations)
            steps.append(f"Calculando: lim({variable}→{point}) {expr}")
            result_val = sp.limit(expr, var, point)
            steps.append(f"Resultado: {result_val}")
            latex_result = sp.latex(result_val)
            interpretation = f"O limite da função quando {variable} tende a {point} é {result_val}."

        elif ct == "equacao":
            parts = expr_str.split("=", 1)
            if len(parts) == 2:
                lhs = parse_expr(parts[0].strip(), local_dict=local_dict, transformations=transformations)
                rhs = parse_expr(parts[1].strip(), local_dict=local_dict, transformations=transformations)
                equation = sp.Eq(lhs, rhs)
                steps.append(f"Equação: {equation}")
                solutions = sp.solve(equation, var)
                steps.append(f"Soluções: {variable} = {solutions}")
                result_val = solutions
                latex_result = ", ".join(sp.latex(s) for s in solutions)
                interpretation = f"A equação possui {len(solutions)} solução(ões): {variable} ∈ {set(solutions)}"
            else:
                expr = parse_expr(expr_str, local_dict=local_dict, transformations=transformations)
                solutions = sp.solve(expr, var)
                result_val = solutions
                latex_result = ", ".join(sp.latex(s) for s in solutions)
                interpretation = f"Raízes: {variable} ∈ {set(solutions)}"

        elif ct == "matriz":
            nums = re.findall(r"-?\d+\.?\d*", expr_str)
            if nums:
                n = int(len(nums) ** 0.5)
                if n * n == len(nums):
                    M = sp.Matrix([float(x) for x in nums]).reshape(n, n)
                    steps.append(f"Matriz {n}×{n}: {M}")
                    det = M.det()
                    eigenvals = M.eigenvals()
                    inv = M.inv() if det != 0 else "Matriz singular (sem inversa)"
                    steps.append(f"Determinante: {det}")
                    steps.append(f"Autovalores: {eigenvals}")
                    steps.append(f"Inversa: {inv}")
                    result_val = {"det": float(det), "eigenvals": str(eigenvals), "inv": str(inv)}
                    latex_result = sp.latex(M)
                    interpretation = f"Determinante={det}. {'Invertível.' if det != 0 else 'Singular (det=0).'}"

        elif ct == "estatistica":
            import numpy as np
            nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", expr_str)]
            if nums:
                media = np.mean(nums)
                mediana = np.median(nums)
                desvio = np.std(nums, ddof=1) if len(nums) > 1 else 0.0
                variancia = np.var(nums, ddof=1) if len(nums) > 1 else 0.0
                steps.extend([
                    f"Dados: {nums}",
                    f"n = {len(nums)}",
                    f"Média: {media:.4f}",
                    f"Mediana: {mediana:.4f}",
                    f"Desvio padrão: {desvio:.4f}",
                    f"Variância: {variancia:.4f}",
                    f"Mín: {min(nums)}, Máx: {max(nums)}",
                ])
                result_val = {"mean": media, "median": mediana, "std": desvio, "var": variancia}
                interpretation = f"Dataset com {len(nums)} valores. Média={media:.2f}, dispersão σ={desvio:.2f}."

        else:
            expr = parse_expr(expr_str, local_dict=local_dict, transformations=transformations)
            steps.append(f"Expressão: {expr}")
            simplified = sp.simplify(expr)
            numeric = None
            try:
                numeric = float(sp.N(simplified))
            except Exception:
                pass
            result_val = simplified
            steps.append(f"Simplificado: {simplified}")
            if numeric is not None:
                steps.append(f"Valor numérico: {numeric:.6f}")
            latex_result = sp.latex(simplified)
            interpretation = f"Expressão simplificada: {simplified}"

        return {
            "result": str(result_val),
            "steps": steps,
            "latex": latex_result,
            "interpretation": interpretation,
            "compute_type": ct,
            "error": None,
        }

    except Exception as exc:
        logger.warning("SymPy compute error for '%s': %s", expression, exc)
        return {
            "result": None,
            "steps": [],
            "latex": "",
            "interpretation": "",
            "compute_type": compute_type,
            "error": str(exc),
        }


# ============================================================
# Code sandbox
# ============================================================

_SANDBOX_BLOCKED_PATTERNS = [
    r"\bimport\s+os\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bimport\s+shutil\b",
    r"\bimport\s+pathlib\b",
    r"\bimport\s+glob\b",
    r"\bimport\s+importlib\b",
    r"\bimport\s+pickle\b",
    r"\bimport\s+ctypes\b",
    r"\bimport\s+threading\b",
    r"\bimport\s+multiprocessing\b",
    r"\bimport\s+asyncio\b",
    r"\bfrom\s+os\b",
    r"\bfrom\s+subprocess\b",
    r"\bfrom\s+socket\b",
    r"\b__import__\s*\(",
    r"\bopen\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bcompile\s*\(",
    r"\bgetattr\s*\(",
    r"\bsetattr\s*\(",
    r"\b__builtins__\b",
    r"\b__class__\b.*\b__subclasses__\b",
]


def _sandbox_security_check(code: str) -> tuple[bool, str]:
    """Retorna (ok, motivo). Bloqueia padrões perigosos."""
    for pattern in _SANDBOX_BLOCKED_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"Padrão não permitido detectado: `{pattern}`"
    # Limite de tamanho
    if len(code) > 8000:
        return False, "Código excede limite de 8000 caracteres."
    return True, ""


def _run_python_sandbox(code: str, timeout: int = 10) -> dict:
    """Executa Python em subprocess com timeout e verificação de segurança."""
    ok, reason = _sandbox_security_check(code)
    if not ok:
        return {
            "stdout": "",
            "stderr": f"Bloqueado por segurança: {reason}",
            "exit_code": -2,
            "error": f"Código bloqueado: {reason}",
        }

    safe_imports = textwrap.dedent("""
import sys, math, cmath, statistics, itertools, functools, collections, random, decimal, fractions
try:
    import numpy as np
except ImportError:
    pass
try:
    import sympy as sp
    from sympy import symbols, solve, diff, integrate, limit, Matrix, latex
except ImportError:
    pass
""")
    full_code = safe_imports + "\n" + code
    fname = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(full_code)
            fname = f.name
        result = subprocess.run(
            [sys.executable, fname],
            capture_output=True,
            text=True,
            timeout=timeout,
            # Isolamento extra: sem herdar variáveis de ambiente sensíveis
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp"},
        )
        return {
            "stdout": result.stdout[:4000],
            "stderr": result.stderr[:2000],
            "exit_code": result.returncode,
            "error": None,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "", "exit_code": -1, "error": f"Timeout ({timeout}s)"}
    except Exception as exc:
        return {"stdout": "", "stderr": "", "exit_code": -1, "error": str(exc)}
    finally:
        if fname:
            try:
                import os as _os
                _os.unlink(fname)
            except Exception:
                pass


# ============================================================
# ChatRequest builder
# ============================================================

def _build_chat_request(messages_data: list, max_tokens: int = 8192) -> ChatRequest:
    msgs = []
    for m in messages_data:
        if not isinstance(m, dict):
            continue
        role = m.get("role", "user")
        if role not in ("system", "user", "assistant", "tool"):
            role = "user"
        row = dict(m)
        row["role"] = role
        row["content"] = str(row.get("content", ""))
        msgs.append(ChatMessage.model_validate(row))
    return ChatRequest(model="syntexa-large", messages=msgs, max_tokens=max_tokens)


# ============================================================
# Privacidade & Anonimato — sem auth, sem log
# ============================================================

@router.get("/privacy")
def education_privacy_policy():
    """
    Retorna a política de privacidade e anonimato do módulo educacional.
    Confirma que nenhum dado de alunos é armazenado.
    """
    return {
        "anonymous": True,
        "data_stored": False,
        "session_type": "ephemeral",
        "cookies": False,
        "tracking": False,
        "ip_logged": False,
        "history_persisted": False,
        "policy": (
            "Todas as sessões públicas do módulo educacional são completamente anônimas. "
            "Nenhuma mensagem, histórico, IP ou dado pessoal é armazenado no servidor. "
            "O processamento ocorre em memória temporária e é descartado ao final de cada requisição. "
            "Sessões são identificadas apenas por tokens efêmeros gerados no navegador do usuário, "
            "sem qualquer vinculação a identidade real. "
            "Conformidade: LGPD (Lei 13.709/2018), GDPR e princípios de Privacy by Design."
        ),
        "rights": [
            "Direito ao anonimato total no uso educacional público",
            "Nenhum dado é vendido, compartilhado ou processado para fins comerciais",
            "Sem perfil de comportamento ou rastreamento de sessão",
            "Histórico existe apenas na memória do dispositivo do usuário",
        ],
        "legal_basis": "LGPD Art. 7º, §3º — dados necessários ao serviço sem identificação pessoal",
    }


# ============================================================
# Ciência & Tecnologia — endpoint especializado (público)
# ============================================================

class ScienceRequest(BaseModel):
    area: str = "geral"        # astronomia | bioinformatica | neurociencias | ia | seguranca | quantica | ambiental
    question: str
    level: str = "avancado"
    language: str = "pt"
    history: list = []


SCIENCE_AREAS = {
    "astronomia": "astronomia",
    "bioinformatica": "bioinformatica",
    "neurociencias": "neurociencias",
    "ia": "inteligencia_artificial",
    "inteligencia_artificial": "inteligencia_artificial",
    "seguranca": "seguranca_digital",
    "seguranca_digital": "seguranca_digital",
    "quantica": "computacao_quantica",
    "computacao_quantica": "computacao_quantica",
    "ambiental": "ciencias_ambientais",
    "ciencias_ambientais": "ciencias_ambientais",
    "saude": "saude",
    "economia": "economia",
    "direito": "direito",
    "geral": "geral",
}


@router.post("/science")
def education_science(
    body: ScienceRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Tutor especializado em ciência & tecnologia de ponta — totalmente anônimo."""
    area = (body.area or "geral").lower()
    discipline = SCIENCE_AREAS.get(area, "geral")
    level = (body.level or "avancado").lower()
    lang = (body.language or "pt").lower()

    disc_prompt = DISCIPLINE_SYSTEM.get(discipline, DISCIPLINE_SYSTEM["geral"])
    level_ctx = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["avancado"])
    lang_instr = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["pt"])
    system_prompt = f"{disc_prompt}\n\n{level_ctx}\n\n{lang_instr}{_ADAPTIVE_META}"

    messages_data: list = [{"role": "system", "content": system_prompt}]
    for msg in (body.history or [])[-14:]:
        if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
            messages_data.append({"role": msg["role"], "content": msg["content"]})
    messages_data.append({"role": "user", "content": body.question})

    req = _build_chat_request(messages_data, max_tokens=2048)
    try:
        resp = create_chat_completion(db, req, user=user)
        content = resp.choices[0].message.content if resp.choices else ""
        return {"content": content, "area": area, "discipline": discipline, "anonymous": True}
    except Exception as exc:
        logger.error("Science endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao processar consulta científica")


@router.post("/science/stream")
def education_science_stream(
    body: ScienceRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Tutor científico em streaming — anônimo."""
    area = (body.area or "geral").lower()
    discipline = SCIENCE_AREAS.get(area, "geral")
    level = (body.level or "avancado").lower()
    lang = (body.language or "pt").lower()

    disc_prompt = DISCIPLINE_SYSTEM.get(discipline, DISCIPLINE_SYSTEM["geral"])
    level_ctx = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["avancado"])
    lang_instr = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["pt"])
    system_prompt = f"{disc_prompt}\n\n{level_ctx}\n\n{lang_instr}{_ADAPTIVE_META}"

    messages_data: list = [{"role": "system", "content": system_prompt}]
    for msg in (body.history or [])[-14:]:
        if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
            messages_data.append({"role": msg["role"], "content": msg["content"]})
    messages_data.append({"role": "user", "content": body.question})

    req = _build_chat_request(messages_data, max_tokens=2048)

    def event_stream():
        try:
            for chunk in stream_chat_completion(db, req, user=user):
                yield f"data: {json.dumps({'content': chunk, 'anonymous': True})}\n\n"
        except Exception as exc:
            logger.error("Science stream error: %s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============================================================
# Área ALUNO — público
# ============================================================

_ADAPTIVE_META = (
    "\n\nINSTRUÇÕES DIDÁTICAS PERMANENTES (meta-tutor):\n"
    "1. Se você perceber que o aluno não compreendeu a explicação anterior (perguntas repetidas, "
    "confusão evidente ou feedback 'difícil'), tente uma abordagem completamente diferente: "
    "use uma analogia do cotidiano, um exemplo concreto numérico ou um diagrama ASCII.\n"
    "2. Monitore o histórico da conversa: se o aluno está progredindo, aumente gradualmente a "
    "complexidade e introduza termos técnicos novos.\n"
    "3. Ao final de cada resposta longa, ofereça: (a) uma pergunta de verificação de entendimento "
    "ou (b) um mini-exercício prático.\n"
    "4. Seja sempre encorajador e paciente. Erros são oportunidades de aprendizado."
)

_FEEDBACK_HINTS = {
    "facil": (
        "\n\nFEEDBACK DO ALUNO: achou muito fácil. Aprofunde o nível — introduza mais rigor "
        "matemático, casos especiais e nuances avançadas."
    ),
    "dificil": (
        "\n\nFEEDBACK DO ALUNO: achou difícil. Simplifique: use analogia, exemplo prático do "
        "dia-a-dia e reduza jargão técnico. Reexplique o conceito central de outra forma."
    ),
    "otimo": (
        "\n\nFEEDBACK DO ALUNO: entendeu bem. Mantenha o nível atual e avance naturalmente."
    ),
}


def _build_tutor_system_prompt(discipline: str, level: str, lang: str, mode: str, feedback: Optional[str] = None) -> str:
    disc_prompt = DISCIPLINE_SYSTEM.get(discipline, DISCIPLINE_SYSTEM["geral"])
    level_ctx = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["intermediario"])
    mode_sfx = MODE_SUFFIX.get(mode, "")
    lang_instr = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["pt"])
    feedback_hint = _FEEDBACK_HINTS.get(feedback or "", "")
    return f"{disc_prompt}\n\n{level_ctx}\n\n{lang_instr}{mode_sfx}{_ADAPTIVE_META}{feedback_hint}"


@router.post("/tutor")
def education_tutor(
    request: _Request,
    body: TutorRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Tutor multi-disciplina com níveis de profundidade, suporte multilíngue e IA adaptativa."""
    _edu_tutor_rate_check(request, user)
    discipline = (body.discipline or "geral").lower()
    level = (body.level or "intermediario").lower()
    lang = (body.language or "pt").lower()
    mode = (body.mode or "chat").lower()
    feedback = (body.feedback or "").lower() or None

    system_prompt = _build_tutor_system_prompt(discipline, level, lang, mode, feedback)

    messages_data: list = [{"role": "system", "content": system_prompt}]
    for msg in (body.history or [])[-14:]:
        if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
            messages_data.append({"role": msg["role"], "content": msg["content"]})
    messages_data.append({"role": "user", "content": body.question})

    req = _build_chat_request(messages_data, max_tokens=2048)
    try:
        if not user:
            cache_payload = json.dumps(
                {
                    "d": discipline,
                    "l": level,
                    "lang": lang,
                    "m": mode,
                    "f": feedback,
                    "q": (body.question or "").strip(),
                    "h": (body.history or [])[-6:],
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            digest = hashlib.sha256(cache_payload.encode("utf-8")).hexdigest()
            hit = edu_public_cache_get(digest)
            if hit is not None:
                return {
                    "content": hit,
                    "discipline": discipline,
                    "level": level,
                    "language": lang,
                    "mode": mode,
                    "cached": True,
                }
        resp = create_chat_completion(db, req, user=user)
        content = resp.choices[0].message.content if resp.choices else ""
        if not user and content:
            edu_public_cache_set(
                digest,
                content,
                ttl_sec=int(getattr(settings, "redis_chat_cache_ttl_sec", 180) or 180),
            )
        return {
            "content": content,
            "discipline": discipline,
            "level": level,
            "language": lang,
            "mode": mode,
            "cached": False,
        }
    except Exception as exc:
        logger.error("Tutor error: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao processar pergunta do tutor")


@router.post("/tutor/stream")
def education_tutor_stream(
    request: _Request,
    body: TutorRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Tutor em streaming com IA adaptativa."""
    _edu_tutor_rate_check(request, user)
    discipline = (body.discipline or "geral").lower()
    level = (body.level or "intermediario").lower()
    lang = (body.language or "pt").lower()
    mode = (body.mode or "chat").lower()
    feedback = (body.feedback or "").lower() or None

    system_prompt = _build_tutor_system_prompt(discipline, level, lang, mode, feedback)

    messages_data: list = [{"role": "system", "content": system_prompt}]
    for msg in (body.history or [])[-14:]:
        if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
            messages_data.append({"role": msg["role"], "content": msg["content"]})
    messages_data.append({"role": "user", "content": body.question})

    req = _build_chat_request(messages_data, max_tokens=2048)

    def event_stream():
        try:
            for chunk in stream_chat_completion(db, req, user=user):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as exc:
            logger.error("Tutor stream error: %s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============================================================
# Motor de Cálculo — público
# ============================================================

def _compute_request_cache_key(body: ComputeRequest) -> str:
    raw = json.dumps(
        {
            "e": (body.expression or "").strip(),
            "t": (body.compute_type or "auto").lower(),
            "v": (body.variable or "x").strip(),
            "x": body.extra or {},
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("/compute")
def education_compute(
    request: _Request,
    body: ComputeRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """
    Motor de cálculo simbólico e numérico.
    Tenta SymPy primeiro; se falhar, usa IA para resolver com explicação passo a passo.
    """
    if not user:
        _edu_compute_limiter.check(
            get_client_ip(request),
            detail="Limite do motor de cálculo atingido. Crie uma conta para uso ilimitado.",
        )
    ck = _compute_request_cache_key(body)
    cached_raw = compute_cache_get(ck)
    if cached_raw:
        try:
            return json.loads(cached_raw)
        except json.JSONDecodeError:
            pass

    sympy_result = _sympy_compute(body.expression, body.compute_type, body.variable, body.extra)

    if sympy_result["error"] is None and sympy_result["result"]:
        # SymPy resolveu — pedir IA para explicar o resultado
        explanation_prompt = (
            f"O cálculo '{body.expression}' foi resolvido simbolicamente.\n"
            f"Tipo: {sympy_result['compute_type']}\n"
            f"Resultado: {sympy_result['result']}\n"
            f"Passos: {chr(10).join(sympy_result['steps'])}\n\n"
            "Explique este resultado de forma educacional: o que significa, como foi obtido "
            "e qual a interpretação prática. Seja conciso e didático. Responda em português."
        )
        req = _build_chat_request(
            [{"role": "system", "content": "Você é um professor de matemática altamente especializado."},
             {"role": "user", "content": explanation_prompt}],
            max_tokens=2048,
        )
        try:
            resp = create_chat_completion(db, req, user=user)
            sympy_result["explanation"] = resp.choices[0].message.content if resp.choices else ""
        except Exception:
            sympy_result["explanation"] = ""
        try:
            compute_cache_set(ck, json.dumps(sympy_result, default=str), ttl_sec=900)
        except (TypeError, ValueError):
            pass
        return sympy_result

    # SymPy falhou — usar IA para resolução completa
    fallback_prompt = (
        f"Resolva o seguinte cálculo com todos os passos detalhados:\n\n{body.expression}\n\n"
        "Formato obrigatório:\n"
        "1. Identifique o tipo de problema\n"
        "2. Apresente a fórmula/método utilizado\n"
        "3. Resolva passo a passo (cada etapa numerada)\n"
        "4. Apresente o resultado final\n"
        "5. Interprete o resultado\n\n"
        "Responda em português, com precisão matemática máxima."
    )
    req = _build_chat_request(
        [{"role": "system", "content": "Você é um sistema de computação matemática com precisão de calculadora científica."},
         {"role": "user", "content": fallback_prompt}],
        max_tokens=8192,
    )
    try:
        resp = create_chat_completion(db, req, user=user)
        ai_content = resp.choices[0].message.content if resp.choices else "Não foi possível calcular."
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro no motor de cálculo: {exc}")

    out = {
        "result": None,
        "steps": [],
        "latex": "",
        "interpretation": "",
        "compute_type": body.compute_type,
        "error": None,
        "ai_solution": ai_content,
        "explanation": "",
    }
    try:
        compute_cache_set(ck, json.dumps(out, default=str), ttl_sec=600)
    except (TypeError, ValueError):
        pass
    return out


@router.post("/compute/code")
def education_code_sandbox(
    body: CodeSandboxRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Sandbox de execução de código Python — requer autenticação."""
    code = body.code
    language = (body.language or "python").lower()
    timeout = max(2, min(body.timeout, 30))

    if language == "python":
        exec_result = _run_python_sandbox(code, timeout=timeout)

        if exec_result["error"] or exec_result["exit_code"] != 0:
            err_text = exec_result.get("stderr") or exec_result.get("error") or "Erro desconhecido"
            analysis_prompt = (
                f"O seguinte código Python produziu um erro:\n\n```python\n{code}\n```\n\n"
                f"Erro: {err_text}\n\n"
                "Explique o erro de forma didática e forneça a versão corrigida do código. "
                "Responda em português."
            )
            req = _build_chat_request(
                [{"role": "system", "content": "Você é um depurador Python especialista em ensino de programação."},
                 {"role": "user", "content": analysis_prompt}],
                max_tokens=4096,
            )
            try:
                resp = create_chat_completion(db, req, user=user)
                exec_result["debug_analysis"] = resp.choices[0].message.content if resp.choices else ""
            except Exception:
                exec_result["debug_analysis"] = ""
        else:
            analysis_prompt = (
                f"Analise este código Python:\n\n```python\n{code}\n```\n\n"
                f"Saída: {exec_result.get('stdout', '')}\n\n"
                "Faça análise breve de: (1) O que o código faz, (2) Complexidade Big-O, "
                "(3) Sugestões de melhoria. Seja conciso. Responda em português."
            )
            req = _build_chat_request(
                [{"role": "system", "content": "Você é um especialista em análise de código Python."},
                 {"role": "user", "content": analysis_prompt}],
                max_tokens=2048,
            )
            try:
                resp = create_chat_completion(db, req, user=user)
                exec_result["code_analysis"] = resp.choices[0].message.content if resp.choices else ""
            except Exception:
                exec_result["code_analysis"] = ""

        return exec_result

    # JavaScript — análise por IA (não executamos JS no servidor)
    analysis_prompt = (
        f"Analise este código JavaScript:\n\n```javascript\n{code}\n```\n\n"
        "Explique: (1) o que faz, (2) possíveis erros/bugs, (3) versão melhorada. "
        "Responda em português."
    )
    req = _build_chat_request(
        [{"role": "system", "content": "Você é um especialista em JavaScript e desenvolvimento web."},
         {"role": "user", "content": analysis_prompt}],
        max_tokens=4096,
    )
    try:
        resp = create_chat_completion(db, req, user=user)
        return {"stdout": "", "stderr": "", "exit_code": 0, "error": None,
                "code_analysis": resp.choices[0].message.content if resp.choices else ""}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================
# Área PROFESSOR — autenticado
# ============================================================

@router.post("/teacher/chat")
def teacher_chat(
    body: TeacherChatRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Ferramentas avançadas para professores e pesquisadores."""
    task = (body.task or "pesquisa").lower()
    lang = (body.language or "pt").lower()
    system_prompt = TEACHER_TASKS.get(task, TEACHER_TASKS["pesquisa"])
    lang_instr = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["pt"])
    level_ctx = LEVEL_CONTEXT.get(body.level or "avancado", LEVEL_CONTEXT["avancado"])

    messages_data: list = [{"role": "system", "content": f"{system_prompt}\n\n{level_ctx}\n\n{lang_instr}"}]
    if body.context:
        messages_data.append({"role": "system", "content": f"Contexto da turma/disciplina: {body.context}"})
    messages_data.append({"role": "user", "content": body.content})

    req = _build_chat_request(messages_data, max_tokens=3000)
    try:
        resp = create_chat_completion(db, req, user=user)
        content = resp.choices[0].message.content if resp.choices else ""
        return {"content": content, "task": task}
    except Exception as exc:
        logger.error("Teacher chat error: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao processar solicitação")


@router.post("/teacher/chat/stream")
def teacher_chat_stream(
    body: TeacherChatRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Ferramentas para professor em streaming."""
    task = (body.task or "pesquisa").lower()
    lang = (body.language or "pt").lower()
    system_prompt = TEACHER_TASKS.get(task, TEACHER_TASKS["pesquisa"])
    lang_instr = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["pt"])
    level_ctx = LEVEL_CONTEXT.get(body.level or "avancado", LEVEL_CONTEXT["avancado"])

    messages_data: list = [{"role": "system", "content": f"{system_prompt}\n\n{level_ctx}\n\n{lang_instr}"}]
    if body.context:
        messages_data.append({"role": "system", "content": f"Contexto: {body.context}"})
    messages_data.append({"role": "user", "content": body.content})

    req = _build_chat_request(messages_data, max_tokens=3000)

    def event_stream():
        try:
            for chunk in stream_chat_completion(db, req, user=user):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as exc:
            logger.error("Teacher stream error: %s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/teacher/research")
def teacher_research(
    body: ResearchRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Pesquisa científica avançada: análise de papers, escrita acadêmica, normas ABNT/APA."""
    task = (body.task or "analisar").lower()
    lang = (body.language or "pt").lower()
    system_prompt = RESEARCH_TASKS.get(task, RESEARCH_TASKS["analisar"])
    lang_instr = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["pt"])

    messages_data: list = [{"role": "system", "content": f"{system_prompt}\n\n{lang_instr}"}]
    if body.extra:
        messages_data.append({"role": "system", "content": f"Informação adicional: {body.extra}"})
    messages_data.append({"role": "user", "content": body.content})

    req = _build_chat_request(messages_data, max_tokens=4000)
    try:
        resp = create_chat_completion(db, req, user=user)
        content = resp.choices[0].message.content if resp.choices else ""
        return {"content": content, "task": task, "language": lang}
    except Exception as exc:
        logger.error("Research error: %s", exc)
        raise HTTPException(status_code=500, detail="Erro na ferramenta de pesquisa")


@router.post("/teacher/research/stream")
def teacher_research_stream(
    body: ResearchRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Pesquisa científica em streaming."""
    task = (body.task or "analisar").lower()
    lang = (body.language or "pt").lower()
    system_prompt = RESEARCH_TASKS.get(task, RESEARCH_TASKS["analisar"])
    lang_instr = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["pt"])

    messages_data: list = [{"role": "system", "content": f"{system_prompt}\n\n{lang_instr}"}]
    if body.extra:
        messages_data.append({"role": "system", "content": f"Informação adicional: {body.extra}"})
    messages_data.append({"role": "user", "content": body.content})

    req = _build_chat_request(messages_data, max_tokens=4000)

    def event_stream():
        try:
            for chunk in stream_chat_completion(db, req, user=user):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/teacher/profile")
def get_teacher_profile(user: models.User = Depends(get_current_user)):
    return {
        "email": user.email,
        "full_name": user.full_name or "",
        "subscription_plan": user.subscription_plan,
        "is_admin": user.is_admin,
    }


# ============================================================
# Área GOVERNO — admin
# ============================================================

@router.get("/gov/stats")
def gov_stats(
    user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Painel de indicadores educacionais nacionais."""
    total_users = db.query(models.User).count()
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    total_sessions = 0
    if hasattr(models, "ChatSession"):
        total_sessions = db.query(models.ChatSession).count()

    # Plan distribution
    plans = {}
    for plan_name in ("free", "basic", "medium", "master"):
        plans[plan_name] = db.query(models.User).filter(models.User.subscription_plan == plan_name).count()

    # Agregados reais (usuários/sessões no banco). Não inventamos divisão regional —
    # isso exige integração com dados geográficos ou institucionais.
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_sessions": total_sessions,
        "plan_distribution": plans,
        "disclaimer": (
            "Indicadores regionais e mapas nacionais ainda não estão conectados a bases oficiais. "
            "Os números abaixo refletem apenas usuários e sessões desta instalação."
        ),
        "indicators": {
            "engagement_rate": round((active_users / total_users * 100) if total_users else 0, 1),
            "avg_sessions_per_user": round(total_sessions / active_users if active_users else 0, 1),
            "dropout_risk_estimate": round(((total_users - active_users) / total_users * 100) if total_users else 0, 1),
        },
        "regions": [],
    }


@router.post("/gov/report")
def gov_generate_report(
    body: dict,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_admin),
):
    """Relatório educacional automatizado por IA."""
    report_type = body.get("type", "geral")
    period = body.get("period", "mensal")
    region = body.get("region", "nacional")

    system_prompt = (
        "Você é um analista sênior de políticas educacionais do Ministério da Educação do Brasil. "
        "Elabore relatórios executivos completos com: sumário executivo, indicadores quantitativos, "
        "análise qualitativa, comparativo histórico, alertas críticos e recomendações priorizadas. "
        "Use linguagem formal e estruture com headers bem definidos."
    )
    user_prompt = (
        f"Elabore um relatório educacional do tipo '{report_type}' para o período '{period}', "
        f"abrangência: {region}.\n\n"
        "Estrutura obrigatória:\n"
        "## 1. Sumário Executivo\n"
        "## 2. Indicadores de Desempenho\n"
        "## 3. Análise Regional\n"
        "## 4. Fatores de Risco (evasão, baixo desempenho)\n"
        "## 5. Iniciativas em Andamento\n"
        "## 6. Recomendações de Políticas Públicas\n"
        "## 7. Próximos Passos\n"
    )

    req = _build_chat_request(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        max_tokens=3000,
    )
    try:
        content = None
        if job_queue_enabled():
            try:
                content = run_gov_report_sync(req.model_dump_json(), user.id)
            except Exception as exc:
                logger.warning("Relatório gov: fila indisponível, síncrono: %s", exc)
        if content is None:
            resp = create_chat_completion(db, req, user=user)
            content = resp.choices[0].message.content if resp.choices else ""
        return {"report": content, "type": report_type, "period": period, "region": region}
    except Exception as exc:
        logger.error("Gov report error: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao gerar relatório")


@router.post("/gov/predict")
def gov_predict(
    body: GovPredictRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_admin),
):
    """Previsões educacionais com IA (evasão, desempenho, crescimento)."""
    scenario = body.scenario
    system_prompt = (
        "Você é um cientista de dados educacional especializado em modelagem preditiva "
        "e análise de risco em sistemas educacionais. "
        "Forneça análises preditivas baseadas em evidências, com intervalos de confiança, "
        "fatores de risco identificados e intervenções recomendadas."
    )
    user_prompt = (
        f"Gere uma análise preditiva para o cenário: '{scenario}'.\n"
        + (f"Contexto adicional: {body.context}\n" if body.context else "")
        + "\nInclua: (1) Previsão para próximos 6-12 meses, (2) Principais fatores de risco, "
        "(3) Probabilidades estimadas, (4) Intervenções recomendadas, (5) Indicadores de monitoramento."
    )

    req = _build_chat_request(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        max_tokens=2048,
    )
    try:
        resp = create_chat_completion(db, req, user=user)
        content = resp.choices[0].message.content if resp.choices else ""
        return {"prediction": content, "scenario": scenario}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/gov/policy")
def gov_policy(
    body: GovPolicyRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_admin),
):
    """Gerador de políticas públicas educacionais por IA."""
    system_prompt = (
        "Você é um especialista em políticas públicas educacionais com 20 anos de experiência "
        "em sistemas educacionais nacionais e internacionais (MEC, UNESCO, OCDE). "
        "Elabore políticas públicas detalhadas, viáveis, mensuráveis e com base em evidências."
    )
    user_prompt = (
        f"Desafio educacional: {body.challenge}\n"
        + (f"Região: {body.region}\n" if body.region else "")
        + (f"Orçamento disponível: {body.budget}\n" if body.budget else "")
        + "\nElabore uma proposta de política pública com:\n"
        "1. Diagnóstico do problema\n"
        "2. Objetivos SMART\n"
        "3. Estratégias de intervenção\n"
        "4. Orçamento estimado por ação\n"
        "5. Cronograma de implementação\n"
        "6. Indicadores de monitoramento e avaliação\n"
        "7. Riscos e mitigações\n"
        "8. Benchmarks internacionais comparáveis\n"
    )

    req = _build_chat_request(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        max_tokens=3000,
    )
    try:
        resp = create_chat_completion(db, req, user=user)
        content = resp.choices[0].message.content if resp.choices else ""
        return {"policy": content, "challenge": body.challenge}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================
# Redação ENEM — correção nas 5 competências (público)
# ============================================================

class EnemEssayRequest(BaseModel):
    essay: str
    theme: Optional[str] = None
    language: str = "pt"


ENEM_COMPETENCIAS = """
Competência 1 — Domínio da modalidade escrita formal da língua portuguesa:
Avalie: ortografia, acentuação, pontuação, concordância verbal e nominal, regência, crase, coesão sintática.

Competência 2 — Compreensão da proposta e aplicação de conceitos das áreas do conhecimento:
Avalie: domínio do tema, abordagem adequada ao gênero dissertativo-argumentativo, uso de repertório sociocultural.

Competência 3 — Seleção, relação, organização e interpretação de informações:
Avalie: estrutura textual (introdução, desenvolvimento, conclusão), coerência argumentativa, progressão temática.

Competência 4 — Demonstração de conhecimento dos mecanismos linguísticos:
Avalie: coesão textual, conectivos, operadores argumentativos, referenciação, paragrafação.

Competência 5 — Elaboração de proposta de intervenção:
Avalie: presença, completude (agente, ação, modo/meio, finalidade, detalhamento) e respeito aos direitos humanos.
"""


@router.post("/essay/grade")
def grade_enem_essay(
    body: EnemEssayRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """
    Corrige redação no formato ENEM — 5 competências, nota 0-1000.
    Público e anônimo: nenhum texto é armazenado.
    """
    if len(body.essay.strip()) < 50:
        raise HTTPException(status_code=422, detail="Redação muito curta para avaliação.")

    theme_line = f"Tema proposto: {body.theme}\n\n" if body.theme else ""
    lang_instr = LANG_INSTRUCTION.get(body.language, LANG_INSTRUCTION["pt"])

    system_prompt = (
        "Você é um professor-corretor especialista em redações do ENEM com 15 anos de experiência. "
        "Avalie a redação com máximo rigor e imparcialidade, seguindo estritamente os critérios oficiais do INEP.\n\n"
        + ENEM_COMPETENCIAS
        + "\n\nFormato obrigatório da resposta:\n"
        "## Competência 1 — [nome] • [nota]/200\n[avaliação detalhada]\n\n"
        "## Competência 2 — [nome] • [nota]/200\n[avaliação detalhada]\n\n"
        "## Competência 3 — [nome] • [nota]/200\n[avaliação detalhada]\n\n"
        "## Competência 4 — [nome] • [nota]/200\n[avaliação detalhada]\n\n"
        "## Competência 5 — [nome] • [nota]/200\n[avaliação detalhada]\n\n"
        "---\n## NOTA FINAL: [soma]/1000\n\n"
        "## Pontos Fortes\n[lista]\n\n"
        "## O que Melhorar\n[lista com exemplos concretos do texto]\n\n"
        "## Exemplos de Reformulação\n[2-3 trechos melhorados]\n\n"
        + lang_instr
    )

    user_prompt = theme_line + "REDAÇÃO:\n\n" + body.essay

    req = _build_chat_request(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        max_tokens=3500,
    )
    try:
        resp = create_chat_completion(db, req, user=user)
        content = resp.choices[0].message.content if resp.choices else ""
        # Extract score from response
        score_line = next(
            (ln for ln in content.split("\n") if "NOTA FINAL" in ln.upper()),
            None
        )
        score_raw = None
        if score_line:
            import re as _re
            m = _re.search(r"(\d{2,4})", score_line)
            if m:
                score_raw = int(m.group(1))
        return {
            "feedback": content,
            "score": score_raw,
            "anonymous": True,
            "stored": False,
        }
    except Exception as exc:
        logger.error("ENEM essay grading error: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao corrigir redação.")


@router.post("/essay/grade/stream")
def grade_enem_essay_stream(
    body: EnemEssayRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Correção de redação ENEM em streaming — anônimo."""
    if len(body.essay.strip()) < 50:
        raise HTTPException(status_code=422, detail="Redação muito curta para avaliação.")

    theme_line = f"Tema proposto: {body.theme}\n\n" if body.theme else ""
    lang_instr = LANG_INSTRUCTION.get(body.language, LANG_INSTRUCTION["pt"])

    system_prompt = (
        "Você é um professor-corretor especialista em redações do ENEM com 15 anos de experiência. "
        "Avalie com máximo rigor seguindo os critérios oficiais do INEP.\n\n"
        + ENEM_COMPETENCIAS
        + "\n\nFormato: Competência 1/200, ..., NOTA FINAL/1000, Pontos Fortes, O que Melhorar, Exemplos de Reformulação.\n"
        + lang_instr
    )
    user_prompt = theme_line + "REDAÇÃO:\n\n" + body.essay

    req = _build_chat_request(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        max_tokens=3500,
    )

    def event_stream():
        try:
            for chunk in stream_chat_completion(db, req, user=user):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============================================================
# Concursos Públicos — tutor especializado (público)
# ============================================================

class ConcursosRequest(BaseModel):
    exam: str = "enem"          # enem | oab | residencia | fuvest | enade | concurso_geral
    subject: str = "geral"
    question: str
    level: str = "avancado"
    language: str = "pt"
    history: list = []


EXAM_CONTEXTS = {
    "enem": (
        "Você é um especialista no ENEM (Exame Nacional do Ensino Médio). "
        "Domina as 4 áreas de conhecimento: Linguagens, Matemática, Ciências da Natureza e Ciências Humanas. "
        "Conhece profundamente a metodologia de cada questão, as competências e habilidades avaliadas (BNCC), "
        "e as tendências dos últimos 10 anos de provas. Para questões, apresente resolução passo a passo "
        "com alternativa correta e justificativa das incorretas."
    ),
    "oab": (
        "Você é um professor de direito especialista no Exame da OAB (Ordem dos Advogados do Brasil). "
        "Cobre: Direito Constitucional, Civil, Penal, Trabalhista, Tributário, Administrativo, Processual Civil e Penal. "
        "Cita o dispositivo legal (Lei, artigo, §) e jurisprudência dos tribunais superiores (STF, STJ, TST). "
        "Responde objetiva e tecnicamente, no formato exigido pela FGV/CESPE."
    ),
    "residencia": (
        "Você é um especialista em Residência Médica. "
        "Cobre: Clínica Médica, Cirurgia, Pediatria, Ginecologia-Obstetrícia, Psiquiatria, Medicina de Família. "
        "Apresenta casos clínicos com diagnóstico diferencial, conduta baseada em evidências (medicina baseada em evidências), "
        "e citação de guidelines (PCDT, UpToDate, ACLS, ATLS). Responde no formato SUSep/UNIFESP/USP."
    ),
    "fuvest": (
        "Você é um especialista na FUVEST e vestibulares de universidades públicas brasileiras (UNICAMP, UNESP, UERJ). "
        "Conhece o estilo discursivo dessas provas, com questões de interpretação profunda, interdisciplinaridade "
        "e exigência de repertório cultural. Para dissertativas, modela a resposta completa com critérios de correção."
    ),
    "enade": (
        "Você é um especialista no ENADE (Exame Nacional de Desempenho dos Estudantes). "
        "Cobre todas as áreas de formação superior: Engenharias, Computação, Saúde, Humanas, Exatas. "
        "Questões com enfoque em competências profissionais, interdisciplinaridade e formação cidadã."
    ),
    "concurso_geral": (
        "Você é um especialista em concursos públicos federais e estaduais do Brasil. "
        "Cobre: Raciocínio Lógico, Português, Matemática Financeira, Conhecimentos Gerais, Direito Administrativo, "
        "Atualidades, Informática e as disciplinas específicas de cada cargo. "
        "Segue o estilo das principais bancas: CESPE/CEBRASPE, FCC, VUNESP, FGV, AOCP."
    ),
}


@router.post("/concursos/tutor")
def concursos_tutor(
    request: _Request,
    body: ConcursosRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Tutor especializado em concursos públicos e vestibulares — anônimo."""
    if not user:
        _edu_concursos_limiter.check(get_client_ip(request))
    exam = (body.exam or "concurso_geral").lower()
    exam_prompt = EXAM_CONTEXTS.get(exam, EXAM_CONTEXTS["concurso_geral"])
    level_ctx = LEVEL_CONTEXT.get(body.level, LEVEL_CONTEXT["avancado"])
    lang_instr = LANG_INSTRUCTION.get(body.language, LANG_INSTRUCTION["pt"])
    disc_ctx = DISCIPLINE_SYSTEM.get(body.subject, "") if body.subject != "geral" else ""

    system = f"{exam_prompt}\n\n{disc_ctx}\n\n{level_ctx}\n\n{lang_instr}"

    messages_data: list = [{"role": "system", "content": system}]
    for msg in (body.history or [])[-12:]:
        if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
            messages_data.append({"role": msg["role"], "content": msg["content"]})
    messages_data.append({"role": "user", "content": body.question})

    req = _build_chat_request(messages_data, max_tokens=2500)
    try:
        resp = create_chat_completion(db, req, user=user)
        content = resp.choices[0].message.content if resp.choices else ""
        return {"content": content, "exam": exam, "anonymous": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/concursos/tutor/stream")
def concursos_tutor_stream(
    request: _Request,
    body: ConcursosRequest,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Tutor de concursos em streaming — anônimo."""
    if not user:
        _edu_concursos_limiter.check(get_client_ip(request))
    exam = (body.exam or "concurso_geral").lower()
    exam_prompt = EXAM_CONTEXTS.get(exam, EXAM_CONTEXTS["concurso_geral"])
    level_ctx = LEVEL_CONTEXT.get(body.level, LEVEL_CONTEXT["avancado"])
    lang_instr = LANG_INSTRUCTION.get(body.language, LANG_INSTRUCTION["pt"])
    disc_ctx = DISCIPLINE_SYSTEM.get(body.subject, "") if body.subject != "geral" else ""

    system = f"{exam_prompt}\n\n{disc_ctx}\n\n{level_ctx}\n\n{lang_instr}"

    messages_data: list = [{"role": "system", "content": system}]
    for msg in (body.history or [])[-12:]:
        if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
            messages_data.append({"role": msg["role"], "content": msg["content"]})
    messages_data.append({"role": "user", "content": body.question})

    req = _build_chat_request(messages_data, max_tokens=2500)

    def event_stream():
        try:
            for chunk in stream_chat_completion(db, req, user=user):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
