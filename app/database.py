from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import config
import os

env = os.getenv('FLASK_ENV', 'development')
database_config = config[env]

# Criar engine
engine = create_engine(
    database_config.SQLALCHEMY_DATABASE_URI,
    echo=database_config.SQLALCHEMY_ECHO
)

# Criar SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db():
    """Função para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()