"""INTENÇÃO -> ficheiros reais (xlsx/pdf/docx/csv/txt) + resumo + TTS opcional."""
from __future__ import annotations

import base64
import csv
import io
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from vereda_backend.docs.docx_builder import build_docx_bytes
from vereda_backend.queues.media_jobs import run_pdf_export_sync, run_xlsx_export_sync
from vereda_backend.services.file_generators.ods_generator import rows_matrix_to_ods_bytes
from vereda_backend.services.file_generators.storage import save_generated_bytes
from vereda_backend.services.media_engine import generate_tts_from_text
from vereda_backend.core.text_polish import polish_portuguese_light, strip_llm_markdown_artifacts

_log = logging.getLogger(__name__)


def _preferred_text_provider_for_export() -> Optional[str]:
    """Alinha com o chat: Ollama / HTTP local têm prioridade sobre o núcleo híbrido."""
    from vereda_backend.core.config import settings as _s

    if (_s.ollama_endpoint or "").strip():
        return "ollama"
    if (_s.local_llm_endpoint or "").strip():
        return "local_http"
    if (_s.exllama_endpoint or "").strip():
        return "exllama"
    if (_s.azure_openai_endpoint or "").strip() and (_s.azure_openai_key or "").strip():
        return "azure_openai"
    if (_s.azure_tgi_endpoint or "").strip():
        return "azure_tgi"
    if (_s.remote_llm_endpoint or "").strip():
        return "remote"
    if (_s.openai_endpoint or "").strip() and (_s.openai_api_key or "").strip():
        return "openai"
    return None


def _ensure_assistant_body(user_message: str, assistant_reply: Optional[str]) -> str:
    """
    Se não há texto do assistente (chat) suficiente, gera o corpo com o mesmo LLM do chat (Ollama por defeito).
    Evita PDF/planilhas só com templates quando o utilizador pediu conteúdo concreto.
    """
    a = (assistant_reply or "").strip()
    if len(a) >= 220:
        return a
    u = (user_message or "").strip()
    if len(u) < 28:
        return a
    try:
        from vereda_backend.ai_runtime import llm_engine

        prompt = (
            "Gera apenas o conteúdo pedido (tabelas em texto, listas, cláusulas, valores, cronograma). "
            "Português europeu/brasileiro correcto, vírgulas e acentuação cuidados. "
            "NÃO uses markdown: proibido ** # ` [links](url) ou símbolos estranhos. "
            "Texto corrido e listas com marcadores simples (• ou 1.).\n\nPedido:\n"
            + u[:9500]
        )
        prov = _preferred_text_provider_for_export()
        if prov and llm_engine.has_provider(prov):
            out = llm_engine.chat(
                [{"role": "user", "content": prompt}],
                provider=prov,
                temperature=0.35,
                max_tokens=8192,
            )
        else:
            out = llm_engine.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.35,
                max_tokens=8192,
            )
        got = polish_portuguese_light((out or "").strip())
        if len(got) > 100:
            return got
    except Exception as exc:
        _log.warning("smart_export: geração LLM auxiliar falhou: %s", exc)
    return a


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _parse_money_br(text: str) -> List[float]:
    out: List[float] = []
    for m in re.finditer(
        r"R\$\s*([\d]{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)", text or "", re.I
    ):
        raw = m.group(1).replace(".", "").replace(",", ".")
        try:
            out.append(float(raw))
        except ValueError:
            continue
    return out


def _financial_model(user_message: str) -> Tuple[List[List[Any]], str, str]:
    """Orçamento mensal calculado; usa números do texto se existirem."""
    nums = _parse_money_br(user_message)
    base_income = nums[0] if len(nums) >= 1 else 15000.0
    if len(nums) >= 2:
        scale = nums[1] / max(sum([3500, 800, 2200, 600, 1200, 500, 400]), 1.0)
    else:
        scale = 1.0

    receitas: List[Tuple[str, float]] = [
        ("Salário / rendas fixas", round(base_income * 0.75, 2)),
        ("Outras receitas", round(base_income * 0.25, 2)),
    ]
    despesas_raw = [
        ("Moradia", 3500),
        ("Condomínio / IPTU parcela", 800),
        ("Alimentação", 2200),
        ("Transporte", 600),
        ("Saúde", 1200),
        ("Educação", 500),
        ("Lazer", 400),
        ("Reserva / poupança", 600),
    ]
    despesas = [(a, round(b * scale, 2)) for a, b in despesas_raw]
    total_rec = sum(x[1] for x in receitas)
    total_desp = sum(x[1] for x in despesas)
    saldo = round(total_rec - total_desp, 2)

    rows: List[List[Any]] = [
        ["Tipo", "Categoria", "Valor (R$)"],
    ]
    for c, v in receitas:
        rows.append(["Receita", c, round(v, 2)])
    for c, v in despesas:
        rows.append(["Despesa", c, round(v, 2)])
    rows.append(["", "Total receitas (R$)", round(total_rec, 2)])
    rows.append(["", "Total despesas (R$)", round(total_desp, 2)])
    rows.append(["", "Saldo projetado (R$)", round(saldo, 2)])

    title = "Orçamento financeiro — Syntexa"
    summary = (
        f"Receitas totais R$ {total_rec:,.2f}; despesas R$ {total_desp:,.2f}; "
        f"saldo R$ {saldo:,.2f}. Ficheiros gerados em Excel e PDF (dados calculados)."
    )
    return rows, title, summary


def _user_message_defines_document_body(u: str) -> bool:
    """
    Pedido longo ou com tema (nutrição, treino, etc.): o corpo do ficheiro deve seguir
    o pedido actual — não a última bolha do chat (ex.: biografia anterior).
    """
    t = (u or "").strip()
    if len(t) >= 130:
        return True
    low = t.lower()
    if re.search(
        r"\b(alimenta(ç|c)|nutri(ç|c)|dieta|card(á|a)pio|ectomorfo|mesomorfo|endomorfo|hipertrofia|"
        r"massa muscular|bulking|deficit|super(á|a)vit|macros?|calorias|prote(í|i)na|carboidrat)\b",
        low,
    ):
        return True
    if re.search(
        r"\b(n(ã|a)o quero|nao quero|sem (hist(ó|o)ria|biografia)|n(ã|a)o (é|e) sobre|esquece)\b",
        low,
    ):
        return True
    return False


def _export_primary(user_message: str, assistant_reply: Optional[str]) -> Tuple[str, str]:
    """
    Corpo a colocar em PDF/planilhas: prioriza a última resposta do assistente
    quando o utilizador só manda um comando curto de exportação.
    Retorna (primary_body, merged_user_plus_assistant para parsing de números).
    """
    u = (user_message or "").strip()
    a = (assistant_reply or "").strip()
    merged = f"{u}\n\n{a}".strip() if a else u
    if _user_message_defines_document_body(u):
        return u, merged
    if not a:
        return u, merged
    ul, lu, la = u.lower(), len(u), len(a)
    short_export_cmd = lu <= 280 and bool(
        re.search(
            r"\b(gera|gere|cria|crie|exporta|exporte|manda|mande|faz|faça|faca|baixa|baixar|quero|preciso|dá|dê|me\s+dá)\b",
            ul,
        )
        and re.search(
            r"\b(pdf|planilha|excel|xlsx|csv|word|docx|ods|tabela|lista|documento|arquivo|ficheiro|anexo)\b",
            ul,
        )
    )
    if short_export_cmd or la >= 80 or (la >= 40 and la >= lu):
        return a, merged
    if la >= 40 and lu <= 160:
        return a, merged
    return u, merged


def _generic_table(user_message: str, *, primary_body: str) -> Tuple[List[List[Any]], str, str]:
    """Planilha: conteúdo principal = resposta da IA quando existir."""
    title = "Planilha — Syntexa"
    u = strip_llm_markdown_artifacts((user_message or "").strip()[:2000])
    body = strip_llm_markdown_artifacts((primary_body or "").strip())
    rows: List[List[Any]] = [
        ["Campo", "Valor"],
        ["Conteúdo (resposta)", body[:20000] if body else "(vazio)"],
    ]
    if u and u not in body[:5000]:
        rows.append(["Pedido / contexto", u])
    rows.append(["Gerado em", "Automático"])
    summary = polish_portuguese_light(
        "Planilha gerada a partir da resposta do assistente no chat (Excel, PDF, CSV e TXT)."
        if body
        else "Planilha criada conforme o seu pedido (ficheiros em Excel, PDF, CSV e TXT)."
    )
    return rows, title, summary


def _simple_pdf_doc(primary_body: str, *, user_message: str) -> Tuple[str, List[Dict[str, Any]], str]:
    title = "Documento — Syntexa"
    body = strip_llm_markdown_artifacts((primary_body or "").strip()[:12000]) or "(vazio)"
    sections: List[Dict[str, Any]] = [{"heading": "Conteúdo", "body": body}]
    u = strip_llm_markdown_artifacts((user_message or "").strip())
    if u and u not in body:
        sections.insert(0, {"heading": "Pedido do utilizador", "body": u[:4000]})
    summary = polish_portuguese_light(
        "PDF e Word gerados com o texto da conversa (prioridade: última resposta do assistente)."
    )
    return title, sections, summary


def _document_contract_pack(_user_message: str) -> Tuple[List[Dict[str, Any]], str, str]:
    title = "Contrato — modelo"
    body = (
        "CLÁUSULA 1 — DO OBJETO\n"
        "O presente contrato regula a prestação de serviços acordada entre as partes, "
        "nos termos da legislação brasileira aplicável.\n\n"
        "CLÁUSULA 2 — DO PRAZO\n"
        "O prazo de vigência será conforme acordado em termo aditivo.\n\n"
        "CLÁUSULA 3 — DAS OBRIGAÇÕES\n"
        "As partes obrigam-se ao fiel cumprimento das cláusulas aqui estabelecidas.\n"
    )
    sections = [
        {"heading": "Partes", "body": "CONTRATANTE: [nome, documento].\nCONTRATADO: [nome, documento]."},
        {"heading": "Cláusulas", "body": body},
    ]
    summary = "Modelo de contrato gerado (DOCX e PDF). Revise com advogado antes de usar."
    return sections, title, summary


def run_smart_export(
    user_message: str,
    *,
    generate_audio: bool = True,
    assistant_reply: Optional[str] = None,
) -> Dict[str, Any]:
    msg = (user_message or "").strip()
    assistant_reply = _ensure_assistant_body(msg, assistant_reply)
    primary, merged_text = _export_primary(msg, assistant_reply)
    low = msg.lower()
    files: List[Dict[str, Any]] = []

    verb = re.search(
        r"\b(faz|faça|faca|gera|gere|cria|crie|monta|manda|mande|exporta|exporte|envia|envie|preciso|quero|me\s+manda|dá|dê|me\s+dá)\b",
        low,
    )
    financial_heavy = bool(
        re.search(
            r"(orçamento|orcamento|financeir|receita|despesa|fluxo\s+de\s+caixa|custos?|saldo|balanço|balanco)",
            low,
        )
    )
    sheet_kw = bool(
        re.search(
            r"\b(planilha|excel|xlsx|csv|ods|odf|tabela|lista|cronograma|spreadsheet|folha\s+de\s+c[aá]lculo|folha\s+de\s+calculo)\b",
            low,
        )
    )
    pdf_kw = bool(re.search(r"\b(pdf|\.pdf|documento\s+pdf|arquivo\s+pdf|ficheiro\s+pdf)\b", low))
    docx_kw = bool(
        re.search(r"\b(docx|word|microsoft\s+word|\.docx|documento\s+word)\b", low)
    )

    financial = bool(verb and sheet_kw and financial_heavy)
    generic_sheet = bool(verb and sheet_kw and not financial_heavy)
    generic_pdf = bool(verb and pdf_kw and not sheet_kw)
    generic_docx = bool(verb and docx_kw and not sheet_kw and not pdf_kw)
    manda_arquivo = bool(
        verb
        and (
            (
                re.search(r"\b(manda|mande|envia|envie)\b", low)
                and re.search(r"\b(arquivo|ficheiro|anexo)\b", low)
            )
            or re.search(r"\bme\s+manda\b", low)
            or re.search(r"\b(manda|mande)\s+(um|uma|o|a)?\s*(arquivo|ficheiro)\b", low)
        )
    )
    generic_manda = bool(manda_arquivo and not pdf_kw and not sheet_kw and not docx_kw)

    ods_only = bool(
        verb
        and (
            re.search(r"\bods\b", low)
            or re.search(r"open\s*document\s*spreadsheet", low)
            or re.search(r"planilha\s+(em\s+)?ods\b", low)
            or re.search(
                r"\b(exporta|exporte|gera|gere|cria|crie|faz|faça|faca)\s+.{0,80}\bods\b",
                low,
            )
            or re.search(r"libreoffice\s+calc", low)
            or re.search(r"onlyoffice.{0,40}\bods\b", low)
        )
    )

    doc_contract = bool(
        re.search(
            r"(contrato|currículo|curriculo|relatório|relatorio|cronograma|cv\b|currículo\s+vitae)",
            low,
        )
        and re.search(
            r"(gera|gere|cria|crie|faz|faça|faca|manda|mande|exporta|exporte|envia)",
            low,
        )
        and not generic_pdf
        and not generic_sheet
        and not generic_manda
    )

    if ods_only:
        if financial_heavy:
            if len((primary or "").strip()) >= 400:
                rows, title, summary = _generic_table(msg, primary_body=primary)
            else:
                rows, title, summary = _financial_model(merged_text)
        else:
            rows, title, summary = _generic_table(msg, primary_body=primary)
        ods_b = rows_matrix_to_ods_bytes(title, rows)
        fn_base = re.sub(r"[^\w\-]+", "-", title, flags=re.UNICODE)[:60].strip("-") or "syntexa"
        fid = save_generated_bytes(ods_b, ".ods")
        files_ods: List[Dict[str, Any]] = [
            {
                "kind": "ods",
                "filename": f"{fn_base}.ods",
                "mime": "application/vnd.oasis.opendocument.spreadsheet",
                "data_base64": _b64(ods_b),
                "download_url": f"/api/files/downloads/{fid}",
                "file_id": fid,
            }
        ]
        tts_ods: Dict[str, Any] = {}
        if generate_audio and summary:
            tts_ods = generate_tts_from_text(summary[:3500])
        return {
            "ok": True,
            "intent": "ods",
            "summary": summary + " Ficheiro OpenDocument (.ods) gerado.",
            "files": files_ods,
            "tts": tts_ods,
        }

    if financial:
        if len((primary or "").strip()) >= 400:
            rows, title, summary = _generic_table(msg, primary_body=primary)
        else:
            rows, title, summary = _financial_model(merged_text)
        xlsx_b = run_xlsx_export_sync(
            "Financeiro", rows, header=True, document_title=title
        )
        pdf_sections = [
            {"heading": "Resumo", "body": summary},
            {
                "heading": "Detalhe (mesmos dados da planilha)",
                "body": "",
                "table_rows": [[str(c) for c in r] for r in rows],
            },
        ]
        pdf_b = run_pdf_export_sync(title, pdf_sections, subtitle="Gerado automaticamente — Syntexa")
        docx_sec = [
            {"heading": "Resumo", "body": summary},
            {"heading": "Tabela", "body": "\n".join(["\t".join(str(x) for x in row) for row in rows])},
        ]
        docx_b = build_docx_bytes(title, docx_sec)

        buf = io.StringIO()
        cw = csv.writer(buf)
        for row in rows:
            cw.writerow(row)
        csv_b = buf.getvalue().encode("utf-8-sig")
        txt_b = (summary + "\n\n" + "\n".join(["\t".join(str(x) for x in r) for r in rows])).encode("utf-8")

        files.extend(
            [
                {"kind": "xlsx", "filename": "syntexa-financeiro.xlsx", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "data_base64": _b64(xlsx_b)},
                {"kind": "pdf", "filename": "syntexa-financeiro.pdf", "mime": "application/pdf", "data_base64": _b64(pdf_b)},
                {"kind": "docx", "filename": "syntexa-financeiro.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "data_base64": _b64(docx_b)},
                {"kind": "csv", "filename": "syntexa-financeiro.csv", "mime": "text/csv; charset=utf-8", "data_base64": _b64(csv_b)},
                {"kind": "txt", "filename": "syntexa-financeiro.txt", "mime": "text/plain; charset=utf-8", "data_base64": _b64(txt_b)},
            ]
        )
    elif generic_sheet or generic_manda:
        rows, title, summary = _generic_table(msg, primary_body=primary)
        xlsx_b = run_xlsx_export_sync("Dados", rows, header=True, document_title=title)
        pdf_sections = [
            {"heading": "Resumo", "body": summary},
            {
                "heading": "Dados",
                "body": "",
                "table_rows": [[str(c) for c in r] for r in rows],
            },
        ]
        pdf_b = run_pdf_export_sync(title, pdf_sections, subtitle="Gerado automaticamente — Syntexa")
        docx_sec = [
            {"heading": "Resumo", "body": summary},
            {"heading": "Tabela", "body": "\n".join(["\t".join(str(x) for x in row) for row in rows])},
        ]
        docx_b = build_docx_bytes(title, docx_sec)
        buf = io.StringIO()
        cw = csv.writer(buf)
        for row in rows:
            cw.writerow(row)
        csv_b = buf.getvalue().encode("utf-8-sig")
        txt_b = (summary + "\n\n" + "\n".join(["\t".join(str(x) for x in r) for r in rows])).encode("utf-8")
        files.extend(
            [
                {"kind": "xlsx", "filename": "syntexa-planilha.xlsx", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "data_base64": _b64(xlsx_b)},
                {"kind": "pdf", "filename": "syntexa-planilha.pdf", "mime": "application/pdf", "data_base64": _b64(pdf_b)},
                {"kind": "docx", "filename": "syntexa-planilha.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "data_base64": _b64(docx_b)},
                {"kind": "csv", "filename": "syntexa-planilha.csv", "mime": "text/csv; charset=utf-8", "data_base64": _b64(csv_b)},
                {"kind": "txt", "filename": "syntexa-planilha.txt", "mime": "text/plain; charset=utf-8", "data_base64": _b64(txt_b)},
            ]
        )
    elif generic_pdf:
        title, sections, summary = _simple_pdf_doc(primary, user_message=msg)
        pdf_b = run_pdf_export_sync(title, sections, subtitle="Gerado automaticamente — Syntexa")
        docx_b = build_docx_bytes(title, sections)
        files.extend(
            [
                {"kind": "pdf", "filename": "syntexa-documento.pdf", "mime": "application/pdf", "data_base64": _b64(pdf_b)},
                {"kind": "docx", "filename": "syntexa-documento.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "data_base64": _b64(docx_b)},
            ]
        )
    elif generic_docx:
        title, sections, summary = _simple_pdf_doc(primary, user_message=msg)
        docx_b = build_docx_bytes(title, sections)
        pdf_b = run_pdf_export_sync(title, sections, subtitle="Gerado automaticamente — Syntexa")
        files.extend(
            [
                {"kind": "docx", "filename": "syntexa-documento.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "data_base64": _b64(docx_b)},
                {"kind": "pdf", "filename": "syntexa-documento.pdf", "mime": "application/pdf", "data_base64": _b64(pdf_b)},
            ]
        )
    elif doc_contract:
        if len((primary or "").strip()) >= 160:
            title, sections, summary = _simple_pdf_doc(primary, user_message=msg)
        else:
            sections, title, summary = _document_contract_pack(msg)
        pdf_b = run_pdf_export_sync(title, sections, "Documento gerado — Syntexa")
        docx_b = build_docx_bytes(title, sections)
        files.extend(
            [
                {"kind": "pdf", "filename": "syntexa-documento.pdf", "mime": "application/pdf", "data_base64": _b64(pdf_b)},
                {"kind": "docx", "filename": "syntexa-documento.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "data_base64": _b64(docx_b)},
            ]
        )
    else:
        return {
            "ok": False,
            "detail": "Pedido não reconhecido para exportação automática. Ex.: «gera planilha», «cria pdf», «gera um contrato».",
        }

    tts: Dict[str, Any] = {}
    if not (summary or "").strip() and files:
        summary = "Ficheiros gerados conforme o seu pedido (veja os anexos para transferência)."
    if generate_audio and summary:
        tts = generate_tts_from_text(summary[:3500])

    _intent = "document"
    if financial:
        _intent = "financial"
    elif generic_sheet or generic_manda:
        _intent = "spreadsheet"
    elif generic_pdf or generic_docx:
        _intent = "export"

    return {
        "ok": True,
        "intent": _intent,
        "summary": summary,
        "files": files,
        "tts": tts,
    }
