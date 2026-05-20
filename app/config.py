import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega o .env padrão
load_dotenv()

# Carrega o arquivo de segredos sensíveis (chaves blockchain, etc.)
# Este arquivo NÃO é commitado — contém ALCHEMY_RPC_URL e BLOCKCHAIN_PRIVATE_KEY
_secrets_file = Path(__file__).resolve().parent.parent / "-AHSOKA.env"
if _secrets_file.exists():
    load_dotenv(dotenv_path=_secrets_file, override=True)

class Config:
    """Configuração base"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@127.0.0.1:3306/tcc_db'

class TestingConfig(Config):
    """Configuração para testes"""
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@127.0.0.1:3306/tcc_db_test'
    TESTING = True

class ProductionConfig(Config):
    """Configuração para produção"""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}