from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.ingresso import Ingresso
from app.models.evento import Evento
from app.models.compra import Compra
from app.models.usuario_cliente import UsuarioCliente
from app.routes.auth_routes import token_required
from datetime import datetime

ingressos_bp = Blueprint('ingressos', __name__, url_prefix='/api/ingressos')


# ======================== CREATE - COMPRAR INGRESSOS ========================
@ingressos_bp.route('/comprar', methods=['POST'])
@token_required
def comprar_ingressos():
    """POST /api/ingressos/comprar - Cliente compra ingressos de um evento"""
    db = SessionLocal()

    try:
        data = request.get_json()
        id_cliente = request.usuario_id  # Do token JWT

        if not data.get('id_evento') or not data.get('quantidade'):
            return jsonify({'erro': 'id_evento e quantidade são obrigatórios'}), 400

        # Buscar evento
        evento = db.query(Evento).filter(Evento.id == data['id_evento']).first()
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        # Verificar disponibilidade
        ingressos_vendidos = db.query(Compra).filter(
            Compra.id_evento == evento.id
        ).with_entities(
            db.func.sum(Compra.quantidade_ingressos)
        ).scalar() or 0

        ingressos_disponiveis = evento.quantidade_ingressos - ingressos_vendidos

        if data['quantidade'] > ingressos_disponiveis:
            return jsonify({
                'erro': f'Quantidade insuficiente. Disponíveis: {ingressos_disponiveis}'
            }), 400

        # Criar compra
        compra = Compra(
            id_cliente=id_cliente,
            id_evento=evento.id,
            quantidade_ingressos=data['quantidade']
        )

        # Criar ingressos individuais
        ingressos = []
        for i in range(data['quantidade']):
            ingresso = Ingresso(id_evento=evento.id)
            ingressos.append(ingresso)

        db.add(compra)
        db.add_all(ingressos)
        db.commit()

        return jsonify({
            'mensagem': 'Ingressos comprados com sucesso',
            'id_compra': compra.id,
            'quantidade': data['quantidade'],
            'evento': evento.nome,
            'ingressos_ids': [ing.id for ing in ingressos]
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== READ - LISTAR INGRESSOS DO CLIENTE ========================
@ingressos_bp.route('/meus-ingressos', methods=['GET'])
@token_required
def meus_ingressos():
    """GET /api/ingressos/meus-ingressos - Listar ingressos do cliente logado"""
    db = SessionLocal()

    try:
        id_cliente = request.usuario_id

        # Buscar compras do cliente
        compras = db.query(Compra).filter(Compra.id_cliente == id_cliente).all()

        if not compras:
            return jsonify({'mensagem': 'Nenhum ingresso encontrado'}), 404

        resultado = []
        for compra in compras:
            # Buscar ingressos dessa compra
            ingressos = db.query(Ingresso).filter(
                Ingresso.id_evento == compra.id_evento
            ).all()

            resultado.append({
                'id_compra': compra.id,
                'evento': compra.evento.nome,
                'quantidade': compra.quantidade_ingressos,
                'ingressos': [{'id': ing.id} for ing in ingressos],
                'data_compra': compra.id  # você pode adicionar um campo de timestamp
            })

        return jsonify({'ingressos': resultado, 'total': len(resultado)}), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== READ - LISTAR INGRESSOS DE UM EVENTO ========================
@ingressos_bp.route('/evento/<int:evento_id>', methods=['GET'])
def listar_ingressos_evento(evento_id):
    """GET /api/ingressos/evento/{evento_id} - Listar todos os ingressos de um evento"""
    db = SessionLocal()

    try:
        evento = db.query(Evento).filter(Evento.id == evento_id).first()
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        ingressos = db.query(Ingresso).filter(Ingresso.id_evento == evento_id).all()

        # Contar quantidade vendida
        quantidade_vendida = db.query(Compra).filter(
            Compra.id_evento == evento_id
        ).with_entities(
            db.func.sum(Compra.quantidade_ingressos)
        ).scalar() or 0

        disponivel = evento.quantidade_ingressos - quantidade_vendida

        return jsonify({
            'evento': evento.nome,
            'total_ingressos': evento.quantidade_ingressos,
            'vendidos': quantidade_vendida,
            'disponivel': disponivel,
            'ingressos': [{'id': ing.id, 'id_evento': ing.id_evento} for ing in ingressos]
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== READ - BUSCAR INGRESSO ESPECÍFICO ========================
@ingressos_bp.route('/<int:ingresso_id>', methods=['GET'])
def obter_ingresso(ingresso_id):
    """GET /api/ingressos/{ingresso_id} - Obter detalhes de um ingresso"""
    db = SessionLocal()

    try:
        ingresso = db.query(Ingresso).filter(Ingresso.id == ingresso_id).first()

        if not ingresso:
            return jsonify({'erro': 'Ingresso não encontrado'}), 404

        return jsonify({
            'id': ingresso.id,
            'id_evento': ingresso.id_evento,
            'evento': ingresso.evento.nome,
            'status': 'ativo'
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== UPDATE - TRANSFERIR INGRESSO ========================
@ingressos_bp.route('/transferir/<int:ingresso_id>', methods=['PUT'])
@token_required
def transferir_ingresso(ingresso_id):
    """PUT /api/ingressos/transferir/{ingresso_id} - Transferir ingresso para outro cliente"""
    db = SessionLocal()

    try:
        data = request.get_json()
        id_cliente_origem = request.usuario_id

        if not data.get('id_cliente_destino'):
            return jsonify({'erro': 'id_cliente_destino é obrigatório'}), 400

        # Buscar ingresso
        ingresso = db.query(Ingresso).filter(Ingresso.id == ingresso_id).first()
        if not ingresso:
            return jsonify({'erro': 'Ingresso não encontrado'}), 404

        # Verificar se cliente destino existe
        cliente_destino = db.query(UsuarioCliente).filter(
            UsuarioCliente.id == data['id_cliente_destino']
        ).first()
        if not cliente_destino:
            return jsonify({'erro': 'Cliente destino não encontrado'}), 404

        # Aqui você poderia implementar lógica de blockchain
        # ingresso.smart_contract()

        return jsonify({
            'mensagem': 'Ingresso transferido com sucesso',
            'ingresso_id': ingresso.id,
            'cliente_origem': id_cliente_origem,
            'cliente_destino': data['id_cliente_destino']
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== DELETE - CANCELAR COMPRA ========================
@ingressos_bp.route('/cancelar/<int:compra_id>', methods=['DELETE'])
@token_required
def cancelar_compra(compra_id):
    """DELETE /api/ingressos/cancelar/{compra_id} - Cancelar uma compra de ingressos"""
    db = SessionLocal()

    try:
        id_cliente = request.usuario_id

        # Buscar compra
        compra = db.query(Compra).filter(Compra.id == compra_id).first()
        if not compra:
            return jsonify({'erro': 'Compra não encontrada'}), 404

        # Verificar se é o cliente da compra
        if compra.id_cliente != id_cliente:
            return jsonify({'erro': 'Você não tem permissão para cancelar esta compra'}), 403

        # Deletar ingressos da compra
        ingressos = db.query(Ingresso).filter(
            Ingresso.id_evento == compra.id_evento
        ).limit(compra.quantidade_ingressos).all()

        for ingresso in ingressos:
            db.delete(ingresso)

        # Deletar compra
        db.delete(compra)
        db.commit()

        return jsonify({
            'mensagem': 'Compra cancelada com sucesso',
            'id_compra': compra_id,
            'quantidade_reembolsada': compra.quantidade_ingressos
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== READ - ESTATÍSTICAS DE VENDAS ========================
@ingressos_bp.route('/evento/<int:evento_id>/estatisticas', methods=['GET'])
def estatisticas_evento(evento_id):
    """GET /api/ingressos/evento/{evento_id}/estatisticas - Estatísticas de vendas do evento"""
    db = SessionLocal()

    try:
        evento = db.query(Evento).filter(Evento.id == evento_id).first()
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        total_vendas = db.query(Compra).filter(
            Compra.id_evento == evento_id
        ).with_entities(
            db.func.sum(Compra.quantidade_ingressos),
            db.func.count(Compra.id)
        ).first()

        quantidade_vendida = total_vendas[0] or 0
        numero_compras = total_vendas[1] or 0

        return jsonify({
            'evento': evento.nome,
            'total_ingressos': evento.quantidade_ingressos,
            'vendidos': quantidade_vendida,
            'disponivel': evento.quantidade_ingressos - quantidade_vendida,
            'numero_compras': numero_compras,
            'percentual_vendido': round((quantidade_vendida / evento.quantidade_ingressos * 100), 2)
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== READ - HISTÓRICO DE COMPRAS ========================
@ingressos_bp.route('/historico', methods=['GET'])
@token_required
def historico_compras():
    """GET /api/ingressos/historico - Ver histórico completo de compras do cliente"""
    db = SessionLocal()

    try:
        id_cliente = request.usuario_id

        compras = db.query(Compra).filter(Compra.id_cliente == id_cliente).all()

        resultado = []
        for compra in compras:
            resultado.append({
                'id_compra': compra.id,
                'evento': compra.evento.nome,
                'quantidade': compra.quantidade_ingressos,
                'data': compra.id  # adicionar timestamp real se tiver
            })

        return jsonify({
            'cliente_id': id_cliente,
            'compras': resultado,
            'total_compras': len(resultado)
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()