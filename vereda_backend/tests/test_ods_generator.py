"""Testes do gerador nativo .ods."""
import io
import zipfile

from vereda_backend.services.file_generators.ods_generator import (
    build_ods_bytes,
    generate_ods,
    rows_matrix_to_ods_bytes,
)


def test_generate_ods_bytes_zip_odf_mimetype():
    raw = build_ods_bytes(
        title="Teste",
        headers=["A", "B"],
        rows=[["1", "2"], ["3", "4"]],
    )
    assert isinstance(raw, bytes)
    assert len(raw) > 100
    assert zipfile.is_zipfile(io.BytesIO(raw))
    z = zipfile.ZipFile(io.BytesIO(raw))
    names = z.namelist()
    assert "mimetype" in names
    assert z.read("mimetype").decode("utf-8").strip() == "application/vnd.oasis.opendocument.spreadsheet"


def test_generate_ods_dict():
    raw = generate_ods(
        {
            "title": "Organização Financeira",
            "headers": ["Categoria", "Valor", "Obs"],
            "rows": [
                ["Salário", 2000, "mensal"],
                ["Combustível", 200, "fixo"],
            ],
        },
        "organizacao.ods",
    )
    assert zipfile.is_zipfile(io.BytesIO(raw))


def test_ods_content_xml_has_cell_values():
    raw = rows_matrix_to_ods_bytes(
        "Matriz",
        [
            ["Nome", "Qtd"],
            ["Item A", 10],
            ["Item B", 20],
        ],
    )
    z = zipfile.ZipFile(io.BytesIO(raw))
    content = z.read("content.xml").decode("utf-8")
    assert "Item A" in content and "Item B" in content and "Nome" in content


def test_resolve_rejects_bad_id():
    from vereda_backend.services.file_generators.storage import resolve_generated_path

    assert resolve_generated_path("../../../etc/passwd", ".ods") is None
    assert resolve_generated_path("not-a-uuid", ".ods") is None
