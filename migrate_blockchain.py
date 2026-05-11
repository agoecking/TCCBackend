import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

migrations = {
    "eventos": [
        ("id_usuario",        "INT NOT NULL DEFAULT 1"),
        ("descricao_evento",  "VARCHAR(280) NOT NULL DEFAULT ''"),
        ("data_hora",         "DATETIME NOT NULL DEFAULT NOW()"),
        ("local_evento",      "VARCHAR(280) NOT NULL DEFAULT ''"),
    ],
    "ingressos": [
        ("token_id",           "INT NULL"),
        ("tx_hash",            "VARCHAR(66) NULL"),
        ("carteira_comprador", "VARCHAR(42) NULL"),
    ],
}

with engine.connect() as conn:
    for table, columns in migrations.items():
        for col, typedef in columns:
            exists = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                f"WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{col}'"
            )).scalar()
            if exists:
                print(f"SKIP  {table}.{col}")
            else:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"))
                conn.commit()
                print(f"OK    {table}.{col}")

print("\nMigracao concluida!")
