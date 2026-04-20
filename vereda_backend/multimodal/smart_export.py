"""INTENÇÃO -> ficheiros reais (xlsx/pdf/docx/csv/txt) + resumo + TTS opcional."""
from __future__ import annotations

import base64
import csv
import io
import re
from typing import Any, Dict, List, Tuple

from vereda_backend.docs.docx_builder import build_docx_bytes
from vereda_backend.queues.media_jobs import run_pdf_export_sync, run_xlsx_export_sync
from vereda_backend.services.media_engine import generate_tts_from_text


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


def _generic_table(user_message: str) -> Tuple[List[List[Any]], str, str]:
    """Planilha simples a partir do pedido (sem tema financeiro explícito)."""
    title = "Planilha — Syntexa"
    u = (user_message or "").strip()
    rows: List[List[Any]] = [
        ["Campo", "Valor"],
        ["Pedido", u[:2000]],
        ["Gerado em", "Automático"],
    ]
    summary = "Planilha criada conforme o seu pedido (ficheiros em Excel, PDF, CSV e TXT)."
    return rows, title, summary


def _simple_pdf_doc(user_message: str) -> Tuple[str, List[Dict[str, Any]], str]:
    title = "Documento — Syntexa"
    body = (user_message or "").strip()[:12000] or "(vazio)"
    sections = [{"heading": "Conteúdo", "body": body}]
    summary = "PDF e Word gerados com o texto do seu pedido."
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


def run_smart_export(user_message: str, *, generate_audio: bool = True) -> Dict[str, Any]:
    msg = (user_message or "").strip()
    low = msg.lower()
    files: List[Dict[str, Any]] = []

    verb = re.search(
        r"\b(faz|faça|faca|gera|gere|cria|crie|monta|manda|mande|exporta|exporte|envia|preciso|quero|me\s+manda)\b",
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
        and re.search(r"\b(manda|mande|envia)\b", low)
        and re.search(r"\b(arquivo|ficheiro|anexo)\b", low)
    )
    generic_manda = bool(manda_arquivo and not pdf_kw and not sheet_kw and not docx_kw)

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

    if financial:
        rows, title, summary = _financial_model(msg)
        xlsx_b = run_xlsx_export_sync("Financeiro", rows, header=True)
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
        rows, title, summary = _generic_table(msg)
        xlsx_b = run_xlsx_export_sync("Dados", rows, header=True)
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
        title, sections, summary = _simple_pdf_doc(msg)
        pdf_b = run_pdf_export_sync(title, sections, subtitle="Gerado automaticamente — Syntexa")
        docx_b = build_docx_bytes(title, sections)
        files.extend(
            [
                {"kind": "pdf", "filename": "syntexa-documento.pdf", "mime": "application/pdf", "data_base64": _b64(pdf_b)},
                {"kind": "docx", "filename": "syntexa-documento.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "data_base64": _b64(docx_b)},
            ]
        )
    elif generic_docx:
        title, sections, summary = _simple_pdf_doc(msg)
        docx_b = build_docx_bytes(title, sections)
        pdf_b = run_pdf_export_sync(title, sections, subtitle="Gerado automaticamente — Syntexa")
        files.extend(
            [
                {"kind": "docx", "filename": "syntexa-documento.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "data_base64": _b64(docx_b)},
                {"kind": "pdf", "filename": "syntexa-documento.pdf", "mime": "application/pdf", "data_base64": _b64(pdf_b)},
            ]
        )
    elif doc_contract:
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
