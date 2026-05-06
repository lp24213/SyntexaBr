"""
Geração nativa de OpenDocument Spreadsheet (.ods) com odfpy.
Compatível com LibreOffice Calc, OpenOffice, OnlyOffice.
"""
from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Mapping, Sequence, Union

from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableCell, TableRow
from odf.text import P


def _cell_text(value: Any) -> TableCell:
    cell = TableCell()
    p = P()
    p.addText("" if value is None else str(value))
    cell.addElement(p)
    return cell


def _normalize_grid(
    headers: Sequence[Any], rows: Sequence[Sequence[Any]]
) -> tuple[list[str], list[list[str]]]:
    hs = ["" if h is None else str(h) for h in headers]
    ncol = max(len(hs), max((len(r) for r in rows), default=0), 1)
    while len(hs) < ncol:
        hs.append("")
    out_rows: list[list[str]] = []
    for r in rows:
        rr = list(r) if r is not None else []
        rr = ["" if x is None else str(x) for x in rr]
        while len(rr) < ncol:
            rr.append("")
        out_rows.append(rr[:ncol])
    return hs[:ncol], out_rows


def build_ods_bytes(*, title: str, headers: Sequence[Any], rows: Sequence[Sequence[Any]]) -> bytes:
    """
    Constrói bytes .ods a partir de cabeçalhos e linhas.
    `title` define o nome da folha (sanitizado).
    """
    hs, grid = _normalize_grid(headers, rows)
    safe_name = re.sub(r"[^\w.\- ]+", "_", (title or "Planilha").strip())[:31] or "Planilha"
    doc = OpenDocumentSpreadsheet()
    table = Table(name=safe_name)

    trh = TableRow()
    for h in hs:
        trh.addElement(_cell_text(h))
    table.addElement(trh)

    for row in grid:
        tr = TableRow()
        for cell in row:
            tr.addElement(_cell_text(cell))
        table.addElement(tr)

    doc.spreadsheet.addElement(table)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def generate_ods(data: Union[Dict[str, Any], Mapping[str, Any]], filename: str) -> bytes:
    """
    API estável: gera .ODS a partir de um dicionário estruturado.

    Parâmetros
    ----------
    data:
        Deve incluir opcionalmente ``title`` (str), ``headers`` (lista),
        ``rows`` (lista de listas). Aceita também chave ``sheet_title`` como alias de title.
    filename:
        Nome sugerido (apenas usado se ``data`` não trouxer título); sanitização no endpoint.

    Retorno
    -------
    bytes do ficheiro .ods (ZIP ODF).
    """
    title = str(
        data.get("title")
        or data.get("sheet_title")
        or data.get("name")
        or "Syntexa"
    ).strip() or "Syntexa"
    headers = list(data.get("headers") or [])
    rows = list(data.get("rows") or [])
    if not rows and not headers:
        headers = ["Coluna A", "Coluna B"]
        rows = [["", ""]]
    return build_ods_bytes(title=title, headers=headers, rows=rows)


def rows_matrix_to_ods_bytes(title: str, matrix: List[List[Any]]) -> bytes:
    """
    Converte uma matriz (primeira linha = cabeçalho) no estilo das exportações smart_export.
    """
    if not matrix:
        return build_ods_bytes(title=title, headers=["—"], rows=[["(vazio)"]])
    headers = matrix[0]
    body = matrix[1:] if len(matrix) > 1 else []
    return build_ods_bytes(title=title, headers=headers, rows=body)
