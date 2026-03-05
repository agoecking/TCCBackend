# import os
# from dotenv import load_dotenv
#
# load_dotenv()
#
# print("HOST:", os.getenv("DB_HOST"))
#
# class Config:
#     SQLALCHEMY_DATABASE_URI = (
#         f"mysql+pymysql://{os.getenv('DB_USER')}:"
#         f"{os.getenv('DB_PASSWORD')}@"
#         f"{os.getenv('DB_HOST')}/"
#         f"{os.getenv('DB_NAME')}"
#     )
#
#     SQLALCHEMY_TRACK_MODIFICATIONS = False

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuração base"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:root@localhost:3306/tccbackend'
    )

class TestingConfig(Config):
    """Configuração para testes"""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
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