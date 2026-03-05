from flask import Flask
from app.config import config


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Registrar rotas
    from app.routes.usuario_routes import usuarios_bp
    app.register_blueprint(usuarios_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8000)  # ✅ Mudei para 8000