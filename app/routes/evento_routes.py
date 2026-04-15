from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.evento import Evento

# NOVO: proteger rotas de escrita
from app.routes.auth_routes import token_required
from app.models.usuario import TipoUsuario

eventos_bp = Blueprint('eventos', __name__, url_prefix='/api/eventos')


@eventos_bp.route('', methods=['GET'])
def listar_eventos():
    """GET /api/eventos - Listar eventos"""
    db = SessionLocal()
    try:
        eventos = db.query(Evento).all()
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
    """POST /api/eventos - Criar evento (somente organização)"""
    # NOVO: checagem de tipo
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode criar evento'}), 403

    db = SessionLocal()
    try:
        data = request.get_json() or {}

        # validação simples
        required = ['nome', 'quantidade_ingressos', 'id_organizacao']
        if not all(k in data for k in required):
            return jsonify({'erro': 'Campos obrigatórios faltando'}), 400

        evento = Evento(
            id=None,
            nome=data['nome'],
            quantidade_ingressos=data['quantidade_ingressos'],
            id_organizacao=data['id_organizacao']
        )

        db.add(evento)
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
    """GET /api/eventos/<id> - Buscar evento"""
    db = SessionLocal()
    try:
        evento = db.query(Evento).filter(Evento.id == id).first()
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
    """PUT /api/eventos/<id> - Atualizar evento (somente organização)"""
    # NOVO: checagem de tipo
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode atualizar evento'}), 403

    db = SessionLocal()
    try:
        evento = db.query(Evento).filter(Evento.id == id).first()
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        data = request.get_json() or {}

        if 'nome' in data:
            evento.nome = data['nome']
        if 'quantidade_ingressos' in data:
            evento.quantidade_ingressos = data['quantidade_ingressos']
        if 'id_organizacao' in data:
            evento.id_organizacao = data['id_organizacao']

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
    """DELETE /api/eventos/<id> - Deletar evento (somente organização)"""
    # NOVO: checagem de tipo
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode deletar evento'}), 403

    db = SessionLocal()
    try:
        evento = db.query(Evento).filter(Evento.id == id).first()
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        db.delete(evento)
        db.commit()

        return jsonify({'mensagem': 'Evento deletado com sucesso'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()