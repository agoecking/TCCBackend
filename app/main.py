from flask import Flask
from app.database import Base, engine
from app.config import config
import os


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Criar tabelas
    Base.metadata.create_all(bind=engine)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)