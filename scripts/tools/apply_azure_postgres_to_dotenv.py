# One-shot: redefina a password de admin do Flexible Server, construa DATABASE_URL, actualize o .env local, imprima a URL
# (sem a password) para SYNTEXA_AZURE_DATABASE_URL — não fazer commit do .env.
# Uso: python scripts/tools/apply_azure_postgres_to_dotenv.py
import os
import re
import secrets
import shutil
import string
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / ".env"

# Azure (do az postgres flexible-server show)
RG = "syntexabr-rg"
SERVER = "syntexabrpg559327"
USER = "syntexaadmin"
HOST = f"{SERVER}.postgres.database.azure.com"
DB = "syntexa"


def strong_pass() -> str:
    s = [secrets.choice(string.ascii_lowercase), secrets.choice(string.ascii_uppercase), secrets.choice(string.digits), "!"]
    for _ in range(28):
        s.append(secrets.choice(string.ascii_letters + string.digits + "!#%&"))
    secrets.SystemRandom().shuffle(s)
    return "".join(s)


def _az_cmd() -> str:
    if sys.platform == "win32":
        return shutil.which("az.cmd") or shutil.which("az") or "az"
    return shutil.which("az") or "az"


def main() -> int:
    pw = strong_pass()
    az = _az_cmd()
    subprocess.run(
        [
            az,
            "postgres",
            "flexible-server",
            "update",
            "-g",
            RG,
            "-n",
            SERVER,
            "--admin-password",
            pw,
        ],
        check=True,
    )
    # Syntexa: coluna VECTOR em messages — requer extensão pgvector (one-shot no servidor)
    subprocess.run(
        [
            az,
            "postgres",
            "flexible-server",
            "parameter",
            "set",
            "-g",
            RG,
            "-s",
            SERVER,
            "-n",
            "azure.extensions",
            "-v",
            "vector",
        ],
        check=True,
    )
    try:
        import psycopg2  # type: ignore

        c = psycopg2.connect(
            host=HOST, user=USER, password=pw, dbname=DB, sslmode="require"
        )
        c.autocommit = True
        cur = c.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        c.close()
    except Exception as e:
        print(f"AVISO: CREATE EXTENSION vector: {e}", file=sys.stderr)

    user_q = quote_plus(USER)
    pw_q = quote_plus(pw)
    url = f"postgresql+psycopg2://{user_q}:{pw_q}@{HOST}:5432/{DB}?sslmode=require"
    if not ENV.is_file():
        print(f"ERRO: falta {ENV}", file=sys.stderr)
        return 1
    text = ENV.read_text(encoding="utf-8", errors="replace")

    for key in ("DATABASE_URL", "VEREDA_DATABASE_URL"):
        if re.search(rf"^{re.escape(key)}=", text, re.M):
            text = re.sub(
                rf"^{re.escape(key)}=.*$",
                lambda _m, k=key, u=url: f"{k}={u}",
                text,
                count=1,
                flags=re.M,
            )
        else:
            text += f"\n{key}={url}\n"
    text = re.sub(r"\n{3,}", "\n\n", text)
    ENV.write_text(text, encoding="utf-8", newline="\n")
    print("OK: .env local actualizado. URL (censurada):")
    print("postgresql+psycopg2://***:***@" f"{HOST}:5432/{DB}?sslmode=require")
    print()
    # Para push script (Bash) usar variável; não escrevemos a URL de outra forma no stdout
    w = os.environ.get("APPLY_AZURE_PG_URL_FILE", str(ROOT / ".syntexa-apply-pg.url.tmp"))
    Path(w).write_text(url, encoding="utf-8")
    print(f"Wrote one-line URL to {w} (delete after) — export: SYNTEXA_AZURE_DATABASE_URL_FILE={w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
