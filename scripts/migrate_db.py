"""
Migração manual do banco SQLite local.
Executa: python scripts/migrate_db.py

Adiciona colunas novas em tabelas existentes sem destruir dados.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./vereda_ai.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})

MIGRATIONS_USERS = {
    "role":               "ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'",
    "subscription_plan":  "ALTER TABLE users ADD COLUMN subscription_plan VARCHAR(32) NOT NULL DEFAULT 'free'",
    "document":           "ALTER TABLE users ADD COLUMN document VARCHAR(32)",
    "cep":                "ALTER TABLE users ADD COLUMN cep VARCHAR(16)",
    "state":              "ALTER TABLE users ADD COLUMN state VARCHAR(64)",
    "city":               "ALTER TABLE users ADD COLUMN city VARCHAR(128)",
    "address_line":       "ALTER TABLE users ADD COLUMN address_line VARCHAR(255)",
    "address_number":     "ALTER TABLE users ADD COLUMN address_number VARCHAR(32)",
    "address_complement": "ALTER TABLE users ADD COLUMN address_complement VARCHAR(255)",
}

def migrate():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    def _b(u: str) -> str:
        if "@" not in u or "://" not in u:
            return u
        head, _sep, rest = u.partition("://")
        if "@" not in rest:
            return f"{head}://***@***{rest[rest.rfind('/'):] if '/' in rest else ''}"
        creds, _at, hostpart = rest.partition("@")
        return f"{head}://***:***@{hostpart}" if "@" in rest else u

    print(f"[migrate] Banco: {_b(DB_URL)}")
    print(f"[migrate] Tabelas encontradas: {sorted(tables)}")

    with engine.connect() as conn:
        if "users" in tables:
            existing = {c["name"] for c in inspector.get_columns("users")}
            for col, sql in MIGRATIONS_USERS.items():
                if col not in existing:
                    try:
                        conn.execute(text(sql))
                        print(f"  [OK] users.{col} adicionada")
                    except Exception as e:
                        print(f"  [SKIP] users.{col}: {e}")
                else:
                    print(f"  [--] users.{col} já existe")
        else:
            print("  [--] Tabela 'users' nao existe ainda (será criada no startup)")

        conn.commit()

    # Cria tabelas novas (institutional_clients, etc.)
    print("\n[migrate] Criando tabelas novas via SQLAlchemy...")
    from vereda_backend.db.session import Base
    from vereda_backend.db import models as _models  # noqa: carrega todos os modelos
    Base.metadata.create_all(bind=engine)
    print("[migrate] Tabelas sincronizadas.")
    print("\n[migrate] CONCLUIDO. Reinicie o backend agora.")

if __name__ == "__main__":
    migrate()
