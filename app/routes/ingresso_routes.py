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
    """
    Comprar ingressos (cliente logado)
    ---
    tags:
      - Ingressos
    summary: Comprar ingressos
    description: Cliente compra ingressos de um evento. Requer JWT no header Authorization.
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
          required: [id_evento, quantidade]
          properties:
            id_evento:
              type: integer
              example: 1
            quantidade:
              type: integer
              example: 2
    responses:
      201:
        description: Compra criada e ingressos gerados
      400:
        description: Erro de validação (campos faltando ou quantidade insuficiente)
      401:
        description: Token não fornecido / inválido
      404:
        description: Evento não encontrado
    """
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
    """
    Listar ingressos do cliente logado
    ---
    tags:
      - Ingressos
    summary: Meus ingressos
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de ingressos (agrupados por compra)
      401:
        description: Token não fornecido / inválido
      404:
        description: Nenhum ingresso encontrado
      400:
        description: Erro
    """
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
    """
    Listar ingressos de um evento
    ---
    tags:
      - Ingressos
    summary: Listar ingressos do evento
    parameters:
      - in: path
        name: evento_id
        type: integer
        required: true
        description: ID do evento
    responses:
      200:
        description: Informações do evento e lista de ingressos
      404:
        description: Evento não encontrado
      400:
        description: Erro
    """
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
    """
    Obter detalhes de um ingresso
    ---
    tags:
      - Ingressos
    summary: Obter ingresso
    parameters:
      - in: path
        name: ingresso_id
        type: integer
        required: true
        description: ID do ingresso
    responses:
      200:
        description: Detalhes do ingresso
      404:
        description: Ingresso não encontrado
      400:
        description: Erro
    """
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
    """
    Transferir ingresso para outro cliente
    ---
    tags:
      - Ingressos
    summary: Transferir ingresso
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: ingresso_id
        type: integer
        required: true
        description: ID do ingresso
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [id_cliente_destino]
          properties:
            id_cliente_destino:
              type: integer
              example: 2
    responses:
      200:
        description: Transferência realizada
      400:
        description: Erro
      401:
        description: Token não fornecido / inválido
      404:
        description: Ingresso ou cliente destino não encontrado
    """
    db = SessionLocal()

    try:
   
      from app.repositories.evento_repository import EventoRepository
      from app.repositories.compra_repository import CompraRepository
      from app.repositories.ingresso_repository import IngressoRepository
      from app.services.ingresso_service import IngressoService
      
      evento_repo = EventoRepository(db)
      compra_repo = CompraRepository(db)
      ingressos_repo = IngressoRepository(db)
      ingressos_service = IngressoService(db, evento_repo, compra_repo, ingressos_repo)

      data = request.get_json()
      nova_propriedade = data['id_cliente_destino']
      meu_id = request.usuario_id

      ingresso = ingressos_service.transferir_ingresso(
        id_ingresso=ingresso_id,
        id_dono_atual=meu_id,
        id_novo_dono=nova_propriedade
      )

      return jsonify({"mensagem": "Ingresso transferido com sucesso!", "novo_dono": ingresso.id_cliente}), 200
    except Exception as e:
      return jsonify({'erro': str(e)}), 400
    finally:
      db.close()
      

# ======================== DELETE - CANCELAR COMPRA ========================
@ingressos_bp.route('/cancelar/<int:compra_id>', methods=['DELETE'])
@token_required
def cancelar_compra(compra_id):
    """
    Cancelar compra
    ---
    tags:
      - Ingressos
    summary: Cancelar compra
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: compra_id
        type: integer
        required: true
        description: ID da compra
    responses:
      200:
        description: Compra cancelada
      401:
        description: Token não fornecido / inválido
      403:
        description: Sem permissão (compra de outro cliente)
      404:
        description: Compra não encontrada
      400:
        description: Erro
    """
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
# @ingressos_bp.route('/evento/<int:evento_id>/estatisticas', methods=['GET'])
# def estatisticas_evento(evento_id):
#     """
#     Estatísticas de vendas do evento
#     ---
#     tags:
#       - Ingressos
#     summary: Estatísticas do evento
#     parameters:
#       - in: path
#         name: evento_id
#         type: integer
#         required: true
#         description: ID do evento
#     responses:
#       200:
#         description: Estatísticas do evento
#       404:
#         description: Evento não encontrado
#       400:
#         description: Erro
#     """
#     db = SessionLocal()
#
#     try:
#         evento = db.query(Evento).filter(Evento.id == evento_id).first()
#         if not evento:
#             return jsonify({'erro': 'Evento não encontrado'}), 404
#
#         total_vendas = db.query(Compra).filter(
#             Compra.id_evento == evento_id
#         ).with_entities(
#             db.func.sum(Compra.quantidade_ingressos),
#             db.func.count(Compra.id)
#         ).first()
#
#         quantidade_vendida = total_vendas[0] or 0
#         numero_compras = total_vendas[1] or 0
#
#         return jsonify({
#             'evento': evento.nome,
#             'total_ingressos': evento.quantidade_ingressos,
#             'vendidos': quantidade_vendida,
#             'disponivel': evento.quantidade_ingressos - quantidade_vendida,
#             'numero_compras': numero_compras,
#             'percentual_vendido': round((quantidade_vendida / evento.quantidade_ingressos * 100), 2)
#         }), 200
#
#     except Exception as e:
#         return jsonify({'erro': str(e)}), 400
#     finally:
#         db.close()


# ======================== READ - HISTÓRICO DE COMPRAS ========================
# @ingressos_bp.route('/historico', methods=['GET'])
# @token_required
# def historico_compras():
#     """
#     Histórico de compras do cliente logado
#     ---
#     tags:
#       - Ingressos
#     summary: Histórico de compras
#     security:
#       - BearerAuth: []
#     responses:
#       200:
#         description: Histórico de compras
#       401:
#         description: Token não fornecido / inválido
#       400:
#         description: Erro
#     """
#     db = SessionLocal()
#
#     try:
#         id_cliente = request.usuario_id
#
#         compras = db.query(Compra).filter(Compra.id_cliente == id_cliente).all()
#
#         resultado = []
#         for compra in compras:
#             resultado.append({
#                 'id_compra': compra.id,
#                 'evento': compra.evento.nome,
#                 'quantidade': compra.quantidade_ingressos,
#                 'data': compra.id  # adicionar timestamp real se tiver
#             })
#
#         return jsonify({
#             'cliente_id': id_cliente,
#             'compras': resultado,
#             'total_compras': len(resultado)
#         }), 200
#
#     except Exception as e:
#         return jsonify({'erro': str(e)}), 400
#     finally:
#         db.close()