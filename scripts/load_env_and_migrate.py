"""
Carrega chaves a partir de um .env (formato chave=valor) e executa scripts/migrate_db.py.
Uso no servidor: cd /opt/syntexa && .venv/bin/python scripts/load_env_and_migrate.py
(Primeira=DATABASE_URL, espelhando VEREDA_DATABASE_URL se faltar, como no remote_deploy.)
"""
import os
import pathlib
import runpy
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"


def load_env() -> None:
    if not ENV.is_file():
        print(f"ERRO: ficheiro .env inexistente: {ENV}", file=sys.stderr)
        raise SystemExit(1)
    text = ENV.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.rstrip("\r\n")
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        if k in ("DATABASE_URL", "VEREDA_DATABASE_URL") and v:
            os.environ[k] = v  # última ocorrência no ficheiro prevalece
    if "DATABASE_URL" not in os.environ and os.environ.get("VEREDA_DATABASE_URL"):
        os.environ["DATABASE_URL"] = os.environ["VEREDA_DATABASE_URL"]


def main() -> None:
    load_env()
    if not (os.environ.get("DATABASE_URL") or "").strip():
        print("ERRO: DATABASE_URL / VEREDA_DATABASE_URL em falta no .env", file=sys.stderr)
        raise SystemExit(1)
    os.environ["PYTHONPATH"] = str(ROOT)
    os.chdir(ROOT)
    p = ROOT / "scripts" / "migrate_db.py"
    if not p.is_file():
        print(f"ERRO: {p} inexistente", file=sys.stderr)
        raise SystemExit(1)
    runpy.run_path(str(p), run_name="__main__")


if __name__ == "__main__":
    main()
