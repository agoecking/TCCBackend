import os
from dotenv import load_dotenv

load_dotenv()

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