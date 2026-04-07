from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.evento import Evento

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
def criar_evento():
    """POST /api/eventos - Criar evento"""
    db = SessionLocal()
    try:
        data = request.get_json()
        
        # O construtor do modelo espera id, nome, quantidade_ingressos, id_organizacao
        # Como o ID real será autoincrementado pelo banco de dados, passamos None ou omitimos caso pudéssemos
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
def atualizar_evento(id):
    """PUT /api/eventos/<id> - Atualizar evento"""
    db = SessionLocal()
    try:
        evento = db.query(Evento).filter(Evento.id == id).first()
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404
            
        data = request.get_json()
        
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
def deletar_evento(id):
    """DELETE /api/eventos/<id> - Deletar evento"""
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
