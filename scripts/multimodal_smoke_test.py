import json
import os
import tempfile
import wave
from datetime import datetime, timezone
from pathlib import Path

import requests

# Worker/Pages pode expor só frontend; rotas /v1/* devem apontar para o backend FastAPI.
BASE = os.environ.get("SYNTEXA_API_BASE", "https://api.syntexabr.com.br").rstrip("/")


def _tiny_png_bytes() -> bytes:
    return bytes.fromhex(
        "89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE"
        "0000000C4944415408D7636060000000020001E221BC330000000049454E44AE426082"
    )


def _tiny_wav_file(path: Path) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 8000)


def _req(method: str, url: str, **kwargs) -> dict:
    try:
        r = requests.request(method, url, timeout=120, **kwargs)
        body = r.content[:800]
        preview = body
        try:
            preview = body.decode("utf-8", errors="replace")
        except Exception:
            preview = str(body)
        data = None
        ct = (r.headers.get("content-type") or "").lower()
        if "json" in ct and r.content:
            try:
                data = r.json()
            except Exception:
                pass
        sig = None
        if r.content[:4] == b"%PDF":
            sig = "pdf"
        elif r.content[:2] == b"PK":
            sig = "zip_office"
        return {
            "ok": 200 <= r.status_code < 300,
            "status": r.status_code,
            "url": url,
            "body_preview": preview[:600],
            "binary_sig": sig,
            "json": data,
        }
    except Exception as exc:
        return {"ok": False, "status": 0, "url": url, "error": str(exc)}


def main() -> int:
    out = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base": BASE,
        "tests": {},
    }

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        img = td_path / "tiny.png"
        wavf = td_path / "tiny.wav"
        img.write_bytes(_tiny_png_bytes())
        _tiny_wav_file(wavf)

        # Mensagem curta — reduz falhas por timeout/carga no chat público
        out["tests"]["public_chat"] = _req(
            "POST",
            f"{BASE}/v1/public-chat",
            json={
                "model": "syntexa",
                "messages": [{"role": "user", "content": "Responda apenas: OK"}],
                "temperature": 0.2,
                "max_tokens": 64,
            },
        )

        out["tests"]["multimodal_ocr"] = _req(
            "POST",
            f"{BASE}/v1/multimodal/ocr",
            files={"file": ("tiny.png", img.read_bytes(), "image/png")},
            data={"kind": "auto"},
        )
        out["tests"]["multimodal_analyze"] = _req(
            "POST",
            f"{BASE}/v1/multimodal/analyze",
            files={"file": ("tiny.png", img.read_bytes(), "image/png")},
            data={"deep": "false"},
        )

        out["tests"]["multimodal_transcribe"] = _req(
            "POST",
            f"{BASE}/v1/multimodal/transcribe",
            files={"file": ("tiny.wav", wavf.read_bytes(), "audio/wav")},
        )

        # Schema real: sections usam "heading" e "body" (ver PdfExportBody + pdf_builder)
        out["tests"]["export_pdf"] = _req(
            "POST",
            f"{BASE}/v1/multimodal/export/pdf",
            json={
                "title": "Relatório Syntexa",
                "subtitle": "Smoke test",
                "sections": [{"heading": "Resumo", "body": "Teste de PDF"}],
            },
        )
        out["tests"]["export_docx"] = _req(
            "POST",
            f"{BASE}/v1/multimodal/export/docx",
            json={
                "title": "Documento Syntexa",
                "sections": [{"heading": "Resumo", "body": "Teste DOCX"}],
            },
        )
        out["tests"]["export_xlsx"] = _req(
            "POST",
            f"{BASE}/v1/multimodal/export/xlsx",
            json={"sheet_title": "Dados", "rows": [["col1", "col2"], [1, 2]], "header": True},
        )
        out["tests"]["export_json"] = _req(
            "POST",
            f"{BASE}/v1/multimodal/json/export",
            json={"title": "JSON Syntexa", "data": {"ok": True}},
        )

        out["tests"]["capabilities"] = _req("GET", f"{BASE}/v1/multimodal/capabilities")

    out_path = Path("docs/MULTIMODAL_SMOKE_REPORT.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_count = sum(1 for t in out["tests"].values() if t.get("ok"))
    total = len(out["tests"])
    pdf_sig = out["tests"].get("export_pdf", {}).get("binary_sig")
    print(f"ok={ok_count}/{total} pdf_sig={pdf_sig} report={out_path}")
    return 0 if ok_count == total else 2


if __name__ == "__main__":
    raise SystemExit(main())
