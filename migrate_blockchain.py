from app.database import engine
from sqlalchemy import text

migrations = [
    "ALTER TABLE ingressos ADD COLUMN token_id INT NULL",
    "ALTER TABLE ingressos ADD COLUMN tx_hash VARCHAR(66) NULL",
    "ALTER TABLE ingressos ADD COLUMN carteira_comprador VARCHAR(42) NULL",
]

with engine.connect() as conn:
    for sql in migrations:
        col = sql.split("ADD COLUMN ")[1].split(" ")[0]
        # Verifica se coluna já existe antes de adicionar
        exists = conn.execute(text(
            f"SELECT COUNT(*) FROM information_schema.columns "
            f"WHERE table_schema=DATABASE() AND table_name='ingressos' AND column_name='{col}'"
        )).scalar()
        if exists:
            print(f"⏭️  {col} já existe, pulando")
        else:
            conn.execute(text(sql))
            conn.commit()
            print(f"✅ {col} adicionado")

print("\nMigração concluída!")
