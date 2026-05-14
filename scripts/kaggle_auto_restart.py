#!/usr/bin/env python3
"""Script para reiniciar notebook Kaggle automaticamente e atualizar Railway.

Uso:
    python scripts/kaggle_auto_restart.py

Requer:
    - KAGGLE_API_TOKEN em ~/.kaggle/kaggle.json
    - RAILWAY_API_TOKEN em env var
    - RAILWAY_SERVICE_ID em env var
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

KAGGLE_USER = "luispaulodeoliveira"
KAGGLE_NOTEBOOK = "syntexa-ai-worker-v2"
KAGGLE_SLUG = f"{KAGGLE_USER}/{KAGGLE_NOTEBOOK}"

RAILWAY_API_TOKEN = os.environ.get("RAILWAY_API_TOKEN", "")
RAILWAY_SERVICE_ID = os.environ.get("RAILWAY_SERVICE_ID", "")


def run_cmd(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERRO: {result.stderr}")
        return ""
    return result.stdout


def push_notebook() -> bool:
    """Faz push do notebook para Kaggle, disparando execucao."""
    print("Fazendo push do notebook Kaggle...")
    edit_dir = Path("C:/Temp/kaggle-edit")
    if not edit_dir.exists():
        print("ERRO: Diretorio kaggle-edit nao encontrado")
        return False

    os.chdir(str(edit_dir))
    output = run_cmd(["kaggle", "kernels", "push"])
    print(output)
    return "404" not in output and "Error" not in output


def wait_for_completion(timeout: int = 1800) -> bool:
    """Espera execucao completar. Timeout em segundos."""
    print("Aguardando execucao...")
    start = time.time()
    while time.time() - start < timeout:
        status = run_cmd(["kaggle", "kernels", "status", KAGGLE_SLUG])
        if "COMPLETE" in status:
            print("Execucao completa!")
            return True
        if "FAILED" in status:
            print("Execucao falhou!")
            return False
        print("Ainda rodando... aguardando 60s")
        time.sleep(60)
    print("Timeout!")
    return False


def get_ngrok_url_from_logs() -> str | None:
    """Baixa log e procura URL do ngrok."""
    log_dir = Path("C:/Temp/kaggle-logs")
    log_dir.mkdir(exist_ok=True)

    run_cmd(["kaggle", "kernels", "output", KAGGLE_SLUG, "-p", str(log_dir)])

    log_file = log_dir / f"{KAGGLE_NOTEBOOK}.log"
    if not log_file.exists():
        return None

    content = log_file.read_text(encoding="utf-8")
    # Procura por URL do ngrok
    match = re.search(r'(https://[a-z0-9]+\.ngrok-free\.app)', content)
    if match:
        return match.group(1)

    # Tambem procura no formato print
    match = re.search(r'Kaggle AI Worker publico: (https://[^\s]+)', content)
    if match:
        return match.group(1)

    return None


def update_railway_variable(url: str) -> bool:
    """Atualiza variavel KAGGLE_INFERENCE_URL_1 no Railway."""
    print(f"Atualizando Railway com URL: {url}")

    # Usa Railway CLI
    env = os.environ.copy()
    env["RAILWAY_API_TOKEN"] = RAILWAY_API_TOKEN

    result = subprocess.run(
        ["railway", "variables", "set", "KAGGLE_INFERENCE_URL_1", url],
        capture_output=True, text=True, env=env,
    )

    if result.returncode == 0:
        print("Railway atualizado com sucesso!")
        return True

    print(f"Erro Railway CLI: {result.stderr}")

    # Fallback: tenta via curl na API do Railway
    try:
        import httpx
        resp = httpx.post(
            "https://backboard.railway.app/graphql/v2",
            headers={
                "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "query": """
                mutation VariableUpsert($input: VariableUpsertInput!) {
                    variableUpsert(input: $input)
                }
                """,
                "variables": {
                    "input": {
                        "serviceId": RAILWAY_SERVICE_ID,
                        "name": "KAGGLE_INFERENCE_URL_1",
                        "value": url,
                    }
                },
            },
        )
        if resp.status_code == 200:
            print("Railway atualizado via API!")
            return True
        print(f"Erro API Railway: {resp.text}")
    except Exception as exc:
        print(f"Erro API Railway: {exc}")

    return False


def main() -> int:
    print("=" * 60)
    print("SYNTEXA AI WORKER - KAGGLE AUTO RESTART")
    print("=" * 60)

    if not RAILWAY_API_TOKEN:
        print("ERRO: RAILWAY_API_TOKEN nao configurado")
        return 1
    if not RAILWAY_SERVICE_ID:
        print("ERRO: RAILWAY_SERVICE_ID nao configurado")
        return 1

    # 1. Push notebook
    if not push_notebook():
        print("Falha no push!")
        return 1

    # 2. Espera completar
    if not wait_for_completion():
        print("Falha na execucao!")
        return 1

    # 3. Pega URL do ngrok
    url = get_ngrok_url_from_logs()
    if not url:
        print("URL do ngrok nao encontrado no log!")
        print("Verifique manualmente em:")
        print(f"https://www.kaggle.com/code/{KAGGLE_SLUG}")
        return 1

    print(f"URL encontrado: {url}")

    # 4. Atualiza Railway
    if not update_railway_variable(url):
        print("Falha ao atualizar Railway!")
        return 1

    print("=" * 60)
    print("SUCESSO! AI Worker rodando em:")
    print(f"  {url}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
