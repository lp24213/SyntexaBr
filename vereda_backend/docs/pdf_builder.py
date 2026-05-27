"""PDF alinhado ao design system do site Syntexa (globals.css / Tailwind) — ReportLab."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from vereda_backend.core.text_polish import strip_llm_markdown_artifacts

# Paleta = frontend/app/globals.css + tailwind (primary #3b82f6, fundo #f8f9fb)
_SITE_BG = colors.HexColor("#F8F9FB")
_SITE_CARD = colors.white
_SITE_BORDER = colors.HexColor("#E5E7EB")
_SITE_TEXT = colors.HexColor("#23272F")
_SITE_MUTED = colors.HexColor("#4B5563")
_SITE_PRIMARY = colors.HexColor("#3B82F6")
_SITE_PRIMARY_DARK = colors.HexColor("#2563EB")
_SITE_PRIMARY_SOFT = colors.HexColor("#EFF6FF")


def _esc(s: str) -> str:
    return (
        strip_llm_markdown_artifacts(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _body_paragraph_flowables(body: str, body_style: ParagraphStyle) -> List[Paragraph]:
    """Quebra texto longo em vários Paragraphs para paginação estável."""
    text = strip_llm_markdown_artifacts(str(body or "")).strip()
    if not text:
        return []
    out: List[Paragraph] = []
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    if not chunks:
        chunks = [text]
    max_chars = 2200
    for chunk in chunks:
        part = chunk
        while len(part) > max_chars:
            slice_end = max_chars
            br = part.rfind(" ", 1600, max_chars)
            if br > 0:
                slice_end = br
            piece = part[:slice_end].strip()
            if piece:
                out.append(Paragraph(_esc(piece).replace("\n", "<br/>"), body_style))
            part = part[slice_end:].strip()
        if part:
            out.append(Paragraph(_esc(part).replace("\n", "<br/>"), body_style))
    return out


def _table_with_wrapping(
    raw_rows: List[List[Any]],
    col_widths: List[float],
    *,
    styles: Any,
    header_row: bool = True,
) -> Table:
    """Todas as células como Paragraph para não cortar texto nas bordas da tabela."""
    cell_norm = ParagraphStyle(
        "TblNorm",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=_SITE_MUTED,
        spaceBefore=0,
        spaceAfter=0,
    )
    cell_hdr = ParagraphStyle(
        "TblHdr",
        parent=cell_norm,
        textColor=_SITE_PRIMARY_DARK,
        fontName="Helvetica-Bold",
        fontSize=9.2,
        leading=12,
    )
    built: List[List[Paragraph]] = []
    for ri, row in enumerate(raw_rows):
        use_hdr = header_row and ri == 0
        st = cell_hdr if use_hdr else cell_norm
        built.append([Paragraph(_esc(str(c if c is not None else "")), st) for c in row])
    t = Table(built, colWidths=col_widths, hAlign="LEFT", repeatRows=1 if header_row else 0, splitByRow=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _SITE_PRIMARY_SOFT),
                ("GRID", (0, 0), (-1, -1), 0.4, _SITE_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_SITE_CARD, _SITE_BG]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def build_pdf_bytes(
    title: str,
    sections: Sequence[Dict[str, Any]],
    subtitle: str | None = None,
) -> bytes:
    """
    sections: [{"heading": str, "body": str, "table_rows": optional [[cell, ...], ...]}, ...]
    """
    buf = io.BytesIO()
    page_w, page_h = A4
    margin_lr = 1.85 * cm
    # Margens maiores: faixa reservada para cabeçalho/rodapé desenhados no canvas (evita “cortar” texto).
    margin_top = 2.45 * cm
    margin_bottom = 2.35 * cm
    usable_w = page_w - 2 * margin_lr

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=margin_lr,
        leftMargin=margin_lr,
        topMargin=margin_top,
        bottomMargin=margin_bottom,
        title=strip_llm_markdown_artifacts((title or "")[:200]),
    )
    styles = getSampleStyleSheet()

    title_clean = strip_llm_markdown_artifacts(title or "Documento")
    subtitle_clean = strip_llm_markdown_artifacts(subtitle or "") if subtitle else ""

    h_cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Heading1"],
        textColor=_SITE_TEXT,
        fontSize=20,
        leading=26,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    h_cover_sub = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        textColor=_SITE_MUTED,
        fontSize=10.5,
        leading=15,
        spaceAfter=4,
    )
    h_cover_accent = ParagraphStyle(
        "CoverAccent",
        parent=styles["Normal"],
        textColor=_SITE_PRIMARY,
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceAfter=0,
    )
    h2 = ParagraphStyle(
        "H2Sec",
        parent=styles["Heading2"],
        textColor=_SITE_PRIMARY_DARK,
        fontSize=13,
        leading=17,
        spaceBefore=8,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7,
        textColor=_SITE_TEXT,
    )

    story: List[Any] = []

    # Capa — visual site: fundo claro, acento azul (sem faixa verde)
    cover_inner = Table(
        [
            [Paragraph(_esc("Syntexa"), h_cover_accent)],
            [Paragraph(_esc(title_clean), h_cover_title)],
        ]
        + (
            [[Paragraph(_esc(subtitle_clean), h_cover_sub)]]
            if subtitle_clean
            else []
        )
        + [
            [Paragraph(_esc("Plano de Negócios — documento para investidores e parceiros"), h_cover_sub)],
        ],
        colWidths=[usable_w - 28],
    )
    cover_inner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _SITE_CARD),
                ("BOX", (0, 0), (-1, -1), 1, _SITE_BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 4, _SITE_PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                ("TOPPADDING", (0, 0), (-1, -1), 22),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 22),
            ]
        )
    )
    cover_shell = Table([[cover_inner]], colWidths=[usable_w])
    cover_shell.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _SITE_BG),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(cover_shell)
    story.append(Spacer(1, 0.45 * cm))
    meta = Table(
        [
            [
                Paragraph(
                    _esc(
                        "Documento institucional · Exportado a partir do site syntexabr.com.br "
                        "· Mantenha confidencialidade conforme acordos em vigor."
                    ),
                    body_style,
                )
            ]
        ],
        colWidths=[usable_w],
    )
    meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _SITE_PRIMARY_SOFT),
                ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#BFDBFE")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 0.6 * cm))
    story.append(PageBreak())

    # Sumário
    toc_title = Paragraph("<b>Sumário</b>", h2)
    toc_raw: List[List[Any]] = [["#", "Capítulo"]]
    for idx, sec in enumerate(sections, start=1):
        head = strip_llm_markdown_artifacts(str(sec.get("heading") or f"Seção {idx}")).strip()
        toc_raw.append([str(idx), head])
    w_num = 1.15 * cm
    toc_table = _table_with_wrapping(toc_raw, [w_num, usable_w - w_num], styles=styles, header_row=True)
    story.append(toc_title)
    story.append(Spacer(1, 0.25 * cm))
    story.append(toc_table)
    story.append(PageBreak())

    for sec in sections:
        head = strip_llm_markdown_artifacts(str(sec.get("heading") or "Seção"))
        body = strip_llm_markdown_artifacts(str(sec.get("body") or ""))
        story.append(Paragraph(f"<b>{_esc(head)}</b>", h2))
        for bp in _body_paragraph_flowables(body, body_style):
            story.append(bp)
        rows = sec.get("table_rows")
        if isinstance(rows, list) and rows:
            data = rows
            if data and isinstance(data[0], (list, tuple)):
                data = [[str(c) if c is not None else "" for c in row] for row in data]
                ncols = max(len(r) for r in data) if data else 1
                col_w = usable_w / float(ncols)
                cw = [col_w for _ in range(ncols)]
                drift = usable_w - sum(cw)
                if abs(drift) > 0.01:
                    cw[-1] += drift
                t = _table_with_wrapping(data, cw, styles=styles, header_row=True)
                story.append(Spacer(1, 0.2 * cm))
                story.append(t)
        story.append(Spacer(1, 0.4 * cm))

    closing_title = Paragraph("<b>Encerramento</b>", h2)
    closing_inner = Table(
        [
            [
                Paragraph(
                    _esc(
                        "Próximos passos sugeridos: (1) alinhamento com investidores e parceiros; "
                        "(2) data room com métricas e documentação jurídica; "
                        "(3) cronograma de implantação e expansão comercial."
                    ),
                    body_style,
                )
            ],
            [Paragraph(_esc("Syntexa — inteligência aplicada à educação, com padrão visual e institucional."), body_style)],
        ],
        colWidths=[usable_w - 24],
    )
    closing_inner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _SITE_CARD),
                ("BOX", (0, 0), (-1, -1), 0.8, _SITE_PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    closing_shell = Table([[closing_inner]], colWidths=[usable_w])
    closing_shell.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), _SITE_BG)]))
    story.append(PageBreak())
    story.append(closing_title)
    story.append(Spacer(1, 0.35 * cm))
    story.append(closing_shell)

    header_y_line = page_h - 1.05 * cm
    header_y_text = page_h - 0.82 * cm
    footer_y_line = 1.5 * cm
    footer_y_text = 1.05 * cm

    def _draw_page(canvas, doc_obj) -> None:
        canvas.saveState()
        p = doc_obj.page
        # Capa (página 1): só rodapé discreto — sem faixa superior a competir com o layout
        if p > 1:
            canvas.setStrokeColor(_SITE_BORDER)
            canvas.setLineWidth(0.6)
            canvas.line(margin_lr, header_y_line, page_w - margin_lr, header_y_line)
            canvas.setFillColor(_SITE_PRIMARY_DARK)
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(margin_lr, header_y_text, "Syntexa")
            canvas.setFillColor(_SITE_MUTED)
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(
                page_w - margin_lr,
                header_y_text,
                strip_llm_markdown_artifacts(title_clean)[:72],
            )
        canvas.setStrokeColor(_SITE_BORDER)
        canvas.line(margin_lr, footer_y_line, page_w - margin_lr, footer_y_line)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(_SITE_MUTED)
        # Rodapé simples: apenas página e data (sem branding Syntexa)
        canvas.drawCentredString(page_w / 2, footer_y_text, f"Página {p}")
        canvas.drawRightString(
            page_w - margin_lr,
            footer_y_text,
            datetime.utcnow().strftime("%d/%m/%Y"),
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buf.getvalue()
