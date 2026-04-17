from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.evento import Evento

from app.routes.auth_routes import token_required
from app.models.usuario import TipoUsuario

from app.repositories.evento_repository import EventoRepository

eventos_bp = Blueprint('eventos', __name__, url_prefix='/api/eventos')


@eventos_bp.route('', methods=['GET'])
def listar_eventos():
    """
    Listar eventos
    ---
    tags:
      - Eventos
    summary: Listar eventos
    responses:
      200:
        description: Lista de eventos
      400:
        description: Erro
    """
    db = SessionLocal()
    try:
        repo = EventoRepository(db)
        eventos = repo.list_all()

        return jsonify([{
            'id': e.id,
            'nome': e.nome,
            'quantidade_ingressos': e.quantidade_ingressos,
            'id_organizacao': e.id_organizacao
        } for e in eventos]), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


@eventos_bp.route('', methods=['POST'])
@token_required
def criar_evento():
    """
    Criar evento (somente ORGANIZAÇÃO)
    ---
    tags:
      - Eventos
    summary: Criar evento
    description: Requer JWT no header Authorization e usuário com tipo ORGANIZACAO.
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [nome, quantidade_ingressos, id_organizacao]
          properties:
            nome:
              type: string
              example: "Evento 1"
            quantidade_ingressos:
              type: integer
              example: 100
            id_organizacao:
              type: integer
              example: 1
    responses:
      201:
        description: Evento criado
      400:
        description: Erro (campos faltando ou falha ao salvar)
      401:
        description: Token não fornecido / inválido
      403:
        description: Apenas ORGANIZAÇÃO pode criar evento
    """
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode criar evento'}), 403

    db = SessionLocal()
    try:
        data = request.get_json() or {}

        required = ['nome', 'quantidade_ingressos', 'id_organizacao']
        if not all(k in data for k in required):
            return jsonify({'erro': 'Campos obrigatórios faltando'}), 400

        repo = EventoRepository(db)

        evento = Evento(
            id=None,
            nome=data['nome'],
            quantidade_ingressos=data['quantidade_ingressos'],
            id_organizacao=data['id_organizacao']
        )

        repo.create(evento)  # em vez de db.add(evento)

        db.commit()
        db.refresh(evento)

        return jsonify({
            'id': evento.id,
            'nome': evento.nome,
            'quantidade_ingressos': evento.quantidade_ingressos,
            'id_organizacao': evento.id_organizacao
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


@eventos_bp.route('/<int:id>', methods=['GET'])
def buscar_evento(id):
    """
    Buscar evento por ID
    ---
    tags:
      - Eventos
    summary: Buscar evento
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID do evento
    responses:
      200:
        description: Evento encontrado
      404:
        description: Evento não encontrado
      400:
        description: Erro
    """
    db = SessionLocal()
    try:
        repo = EventoRepository(db)
        evento = repo.get_by_id(id)  # em vez de db.query(...)

        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        return jsonify({
            'id': evento.id,
            'nome': evento.nome,
            'quantidade_ingressos': evento.quantidade_ingressos,
            'id_organizacao': evento.id_organizacao
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


@eventos_bp.route('/<int:id>', methods=['PUT'])
@token_required
def atualizar_evento(id):
    """
    Atualizar evento (somente ORGANIZAÇÃO)
    ---
    tags:
      - Eventos
    summary: Atualizar evento
    description: Requer JWT no header Authorization e usuário com tipo ORGANIZACAO.
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID do evento
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nome:
              type: string
              example: "Evento Atualizado"
            quantidade_ingressos:
              type: integer
              example: 120
            id_organizacao:
              type: integer
              example: 1
    responses:
      200:
        description: Evento atualizado
      401:
        description: Token não fornecido / inválido
      403:
        description: Apenas ORGANIZAÇÃO pode atualizar evento
      404:
        description: Evento não encontrado
      400:
        description: Erro
    """
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode atualizar evento'}), 403

    db = SessionLocal()
    try:
        repo = EventoRepository(db)
        evento = repo.get_by_id(id)

        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        data = request.get_json() or {}

        if 'nome' in data:
            evento.nome = data['nome']
        if 'quantidade_ingressos' in data:
            evento.quantidade_ingressos = data['quantidade_ingressos']
        if 'id_organizacao' in data:
            evento.id_organizacao = data['id_organizacao']

        # opcional: repo.update(evento) (só se você tiver objeto detached)
        # repo.update(evento)

        db.commit()
        db.refresh(evento)

        return jsonify({
            'id': evento.id,
            'nome': evento.nome,
            'quantidade_ingressos': evento.quantidade_ingressos,
            'id_organizacao': evento.id_organizacao
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


@eventos_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def deletar_evento(id):
    """
    Deletar evento (somente ORGANIZAÇÃO)
    ---
    tags:
      - Eventos
    summary: Deletar evento
    description: Requer JWT no header Authorization e usuário com tipo ORGANIZACAO.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID do evento
    responses:
      200:
        description: Evento deletado
      401:
        description: Token não fornecido / inválido
      403:
        description: Apenas ORGANIZAÇÃO pode deletar evento
      404:
        description: Evento não encontrado
      400:
        description: Erro
    """
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode deletar evento'}), 403

    db = SessionLocal()
    try:
        repo = EventoRepository(db)
        evento = repo.get_by_id(id)

        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        repo.delete(evento)  # em vez de db.delete(evento)
        db.commit()

        return jsonify({'mensagem': 'Evento deletado com sucesso'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()