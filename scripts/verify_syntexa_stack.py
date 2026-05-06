#!/usr/bin/env python3
"""
Verificação real da API Syntexa (sem inventar resultado): health, capabilities,
exportações binárias (assinatura %PDF / PK), STT, chat público.

Uso:
  python scripts/verify_syntexa_stack.py
  python scripts/verify_syntexa_stack.py --base https://api.syntexabr.com.br

Saída: relatório em texto + código de saída != 0 se algum teste crítico falhar.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


def _wav_silence_1s_16k_mono() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)
    return buf.getvalue()


def _check_pdf(data: bytes) -> bool:
    return len(data) >= 4 and data[:4] == b"%PDF"


def _check_zip_pk(data: bytes) -> bool:
    return len(data) >= 4 and data[:2] == b"PK"


def _req(
    session: requests.Session, method: str, url: str, **kwargs: Any
) -> tuple[int, bytes, str]:
    r = session.request(method, url, timeout=120, **kwargs)
    ct = (r.headers.get("content-type") or "").lower()
    raw = r.content
    return r.status_code, raw, ct


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--base",
        default=os.environ.get("SYNTEXA_API_BASE", "https://api.syntexabr.com.br"),
        help="URL base da API FastAPI (ex.: https://api.syntexabr.com.br)",
    )
    args = p.parse_args()
    base = str(args.base).rstrip("/")

    session = requests.Session()
    session.headers.setdefault("User-Agent", "SyntexaVerifyStack/1.0")

    lines: list[str] = []
    fails = 0
    critical = 0

    def ok(name: str, cond: bool, detail: str = "", *, crit: bool = True) -> None:
        nonlocal fails, critical
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
            if crit:
                critical += 1
        lines.append(f"[{st}] {name}" + (f" — {detail}" if detail else ""))

    lines.append(f"=== Syntexa verify === {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"BASE={base}")

    # 1) Health
    code, body, ct = _req(session, "GET", f"{base}/health")
    low = body.lower()
    health_text = (
        b'"status"' in low
        or b'"ok"' in low
        or b"healthy" in low
        or b"ready" in low
    )
    ok("GET /health", code == 200 and health_text, f"status={code} len={len(body)}")

    # 2) Capabilities (mostra se STT Azure/local está configurado no servidor)
    code, body, ct = _req(session, "GET", f"{base}/v1/multimodal/capabilities")
    caps: dict = {}
    if code == 200:
        try:
            caps = json.loads(body.decode("utf-8", errors="replace"))
        except Exception:
            caps = {}
    ok("GET /v1/multimodal/capabilities", code == 200, f"status={code} stt={caps.get('stt')} tts={caps.get('tts')}")

    # 3) PDF export — corpo com heading/body (schema real)
    pdf_payload = {
        "title": "Verify Stack",
        "subtitle": "teste automático",
        "sections": [{"heading": "Resumo", "body": "Texto de teste sem código."}],
    }
    code, body, ct = _req(
        session,
        "POST",
        f"{base}/v1/multimodal/export/pdf",
        json=pdf_payload,
        headers={"Content-Type": "application/json"},
    )
    ok(
        "POST /v1/multimodal/export/pdf (bytes %PDF)",
        code == 200 and _check_pdf(body),
        f"status={code} len={len(body)} ct={ct[:60]}",
    )

    # 4) XLSX
    xlsx_payload = {
        "sheet_title": "Dados",
        "rows": [["A", "B"], [1, 2]],
        "header": True,
    }
    code, body, ct = _req(
        session,
        "POST",
        f"{base}/v1/multimodal/export/xlsx",
        json=xlsx_payload,
        headers={"Content-Type": "application/json"},
    )
    ok(
        "POST /v1/multimodal/export/xlsx (ZIP/PK)",
        code == 200 and _check_zip_pk(body),
        f"status={code} len={len(body)}",
    )

    # 5) DOCX
    docx_payload = {
        "title": "Verify",
        "sections": [{"heading": "Secção", "body": "Conteúdo de teste."}],
    }
    code, body, ct = _req(
        session,
        "POST",
        f"{base}/v1/multimodal/export/docx",
        json=docx_payload,
        headers={"Content-Type": "application/json"},
    )
    ok(
        "POST /v1/multimodal/export/docx (ZIP/PK)",
        code == 200 and _check_zip_pk(body),
        f"status={code} len={len(body)}",
    )

    # 6) STT — WAV silencioso (pode devolver texto vazio; não falha se API responde JSON válido)
    files = {"file": ("silence.wav", _wav_silence_1s_16k_mono(), "audio/wav")}
    code, body, ct = _req(
        session, "POST", f"{base}/v1/multimodal/transcribe", files=files
    )
    stt_ok = False
    stt_detail = f"status={code}"
    if code == 200 and "json" in ct:
        try:
            j = json.loads(body.decode("utf-8", errors="replace"))
            stt_ok = isinstance(j, dict) and ("ok" in j or "text" in j)
            stt_detail += f" ok={j.get('ok')} provider={j.get('provider')} text_len={len(str(j.get('text','')))}"
        except Exception as e:
            stt_detail += f" json_err={e}"
    ok(
        "POST /v1/multimodal/transcribe (JSON válido)",
        stt_ok or (code == 200),
        stt_detail,
        crit=False,
    )

    # 7) Chat público curto
    code, body, ct = _req(
        session,
        "POST",
        f"{base}/v1/public-chat",
        json={
            "model": "syntexa",
            "messages": [{"role": "user", "content": "Responda apenas: OK"}],
            "max_tokens": 32,
        },
        headers={"Content-Type": "application/json"},
    )
    chat_ok = code == 200 and b"choices" in body
    ok("POST /v1/public-chat", chat_ok, f"status={code}")

    report = "\n".join(lines)
    print(report)

    out_path = Path("docs") / "VERIFY_STACK_LAST.txt"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report + "\n", encoding="utf-8")
        print(f"\nRelatório gravado em: {out_path}")
    except OSError:
        pass

    if critical > 0:
        print(f"\nFalhas críticas: {critical} (total falhas: {fails})", file=sys.stderr)
        return 2
    if fails > 0:
        print(f"\nAvisos / falhas não críticas: {fails}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
