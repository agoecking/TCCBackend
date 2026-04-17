from flask import Flask
from app.config import config
from flasgger import Swagger

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,   # inclui todas as rotas
                "model_filter": lambda tag: True,   # inclui todos os models
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "TCCBackend API",
            "version": "1.0.0",
        },
        # (opcional) Bearer auth no Swagger 2.0:
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Use: Bearer <seu_token_jwt>"
            }
        }
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # Registrar rotas
    from app.routes.usuario_routes import usuarios_bp
    app.register_blueprint(usuarios_bp)

    from app.routes.evento_routes import eventos_bp
    app.register_blueprint(eventos_bp)

    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.ingresso_routes import ingressos_bp
    app.register_blueprint(ingressos_bp)

    from app.routes.organizacao_routes import organizacoes_bp
    app.register_blueprint(organizacoes_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8000)