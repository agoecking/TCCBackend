from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.ingresso import Ingresso
from app.models.evento import Evento
from app.models.compra import Compra
from app.models.usuario import TipoUsuario
from app.models.usuario_cliente import UsuarioCliente
from app.routes.auth_routes import token_required
from app.repositories.evento_repository import EventoRepository
from app.repositories.compra_repository import CompraRepository
from app.repositories.ingresso_repository import IngressoRepository
from app.services.ingresso_service import IngressoService
from app.services.errors import ValidationError, NotFoundError
from sqlalchemy import func
from datetime import datetime

ingressos_bp = Blueprint('ingressos', __name__, url_prefix='/api/ingressos')


def _make_ingresso_service(db):
    return IngressoService(
        db=db,
        evento_repo=EventoRepository(db),
        compra_repo=CompraRepository(db),
        ingresso_repo=IngressoRepository(db),
    )


# ======================== [LEGADO] CREATE - COMPRAR INGRESSOS ========================
# ATENÇÃO: rota legada — substituída pelo fluxo MetaMask (/registrar-mint).
# O frontend não chama mais esta rota. Mantida apenas para referência histórica no TCC.
# @ingressos_bp.route('/comprar', methods=['POST'])
# @token_required
def comprar_ingressos():
    """
    Comprar ingressos (cliente logado)
    ---
    tags:
      - Ingressos
    summary: Comprar ingressos
    description: |
      Cliente autenticado compra ingressos de um evento.
      Se o evento tiver blockchain_event_id configurado, cada ingresso é mintado
      como NFT na Sepolia automaticamente após a compra off-chain.
      Requer JWT no header Authorization.
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
        description: Compra criada e ingressos gerados (com NFT se evento tiver blockchain_event_id)
      400:
        description: Erro de validação
      401:
        description: Token não fornecido / inválido
      403:
        description: Apenas clientes podem comprar ingressos
      404:
        description: Evento não encontrado
    """
    db = SessionLocal()

    try:
        data = request.get_json() or {}
        id_cliente = request.usuario_id

        # Apenas clientes compram ingressos — organizações não
        if request.usuario_tipo != TipoUsuario.CLIENTE:
            return jsonify({'erro': 'Apenas clientes podem comprar ingressos'}), 403

        if not data.get('id_evento') or not data.get('quantidade'):
            return jsonify({'erro': 'id_evento e quantidade são obrigatórios'}), 400

        service = _make_ingresso_service(db)
        resultado = service.comprar_ingressos(
            id_cliente=id_cliente,
            id_evento=data['id_evento'],
            quantidade=data['quantidade'],
        )

        return jsonify({
            'mensagem': 'Ingressos comprados com sucesso',
            **resultado,
        }), 201

    except (ValidationError, NotFoundError) as e:
        return jsonify({'erro': str(e)}), 400
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

        ingressos = db.query(Ingresso).filter(Ingresso.id_cliente == id_cliente).all()

        if not ingressos:
            return jsonify({'ingressos': [], 'total': 0}), 200

        # Agrupa por evento
        eventos_map: dict = {}
        for ing in ingressos:
            ev_id = ing.id_evento
            if ev_id not in eventos_map:
                eventos_map[ev_id] = {
                    'evento': ing.evento.nome if ing.evento else f'Evento #{ev_id}',
                    'ingressos': []
                }
            eventos_map[ev_id]['ingressos'].append({
                'id': ing.id,
                'id_evento': ing.id_evento,
                'status': ing.status,
                'token_id': ing.token_id,
                'tx_hash': ing.tx_hash,
                'carteira_comprador': ing.carteira_comprador,
                'resale_price_wei': ing.resale_price_wei,
                'max_resale_price_wei': ing.evento.max_resale_price_wei if ing.evento else None,
            })

        resultado = list(eventos_map.values())
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

        # Contar quantidade vendida direto na tabela Ingresso
        # (mints via MetaMask não criam Compra, então contar por Compra era incorreto)
        quantidade_vendida = db.query(Ingresso).filter(
            Ingresso.id_evento == evento_id,
            Ingresso.status != 'disponivel'
        ).count()

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
            'evento': ingresso.evento.nome if ingresso.evento else None,
            'status': ingresso.status,
            'token_id': ingresso.token_id,
            'tx_hash': ingresso.tx_hash,
            'carteira_comprador': ingresso.carteira_comprador,
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
      

# ======================== [LEGADO] DELETE - CANCELAR COMPRA ========================
# ATENÇÃO: rota legada — dependia do fluxo /comprar que foi substituído por /registrar-mint.
# Mantida apenas para referência histórica no TCC.
# @ingressos_bp.route('/cancelar/<int:compra_id>', methods=['DELETE'])
# @token_required
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


# ======================== POST - ANUNCIAR REVENDA ========================
@ingressos_bp.route('/<int:ingresso_id>/anunciar-revenda', methods=['POST'])
@token_required
def anunciar_revenda(ingresso_id):
    """
    Anunciar ingresso para revenda
    ---
    tags:
      - Ingressos
    summary: Anunciar revenda
    description: |
      Registra o ingresso como à venda no banco após o frontend assinar listForResale()
      via MetaMask. O tx_hash da transação on-chain é salvo para rastreabilidade.
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: ingresso_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [price_wei, tx_hash]
          properties:
            price_wei:
              type: integer
              example: 1500000000000000
              description: "Preço de revenda em wei"
            tx_hash:
              type: string
              description: "Hash da transação listForResale() já assinada via MetaMask"
    responses:
      200:
        description: Ingresso anunciado para revenda
      400:
        description: Erro de validação
      401:
        description: Token não fornecido / inválido
      403:
        description: Apenas clientes podem anunciar revenda
    """
    if request.usuario_tipo != TipoUsuario.CLIENTE:
        return jsonify({'erro': 'Apenas clientes podem anunciar revenda'}), 403

    db = SessionLocal()
    try:
        data = request.get_json() or {}
        price_wei = data.get('price_wei')
        tx_hash = data.get('tx_hash')

        if price_wei is None:
            return jsonify({'erro': 'price_wei é obrigatório'}), 400
        if not tx_hash:
            return jsonify({'erro': 'tx_hash é obrigatório (assine via MetaMask antes)'}), 400

        service = _make_ingresso_service(db)
        ingresso = service.anunciar_revenda(
            id_ingresso=ingresso_id,
            id_dono=request.usuario_id,
        )

        ingresso.resale_price_wei = str(price_wei)
        ingresso.tx_hash = tx_hash  # atualiza com o hash da transação de listagem
        db.commit()

        return jsonify({
            'mensagem': 'Ingresso anunciado para revenda',
            'ingresso_id': ingresso.id,
            'token_id': ingresso.token_id,
            'resale_price_wei': str(price_wei),
            'tx_hash': tx_hash,
        }), 200

    except (ValidationError, NotFoundError) as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== GET - LISTAR REVENDAS DE UM EVENTO ========================
@ingressos_bp.route('/evento/<int:evento_id>/revenda', methods=['GET'])
def listar_revenda_evento(evento_id):
    """
    Listar ingressos à venda no mercado de revenda de um evento
    ---
    tags:
      - Ingressos
    parameters:
      - in: path
        name: evento_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de ingressos em revenda
    """
    db = SessionLocal()
    try:
        ingressos = db.query(Ingresso).filter(
            Ingresso.id_evento == evento_id,
            Ingresso.status == 'a_venda'
        ).all()

        return jsonify({
            'revendas': [{
                'id': ing.id,
                'token_id': ing.token_id,
                'resale_price_wei': ing.resale_price_wei,
                'carteira_vendedor': ing.carteira_comprador,
            } for ing in ingressos]
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== POST - COMPRAR REVENDA ========================
@ingressos_bp.route('/<int:ingresso_id>/comprar-revenda', methods=['POST'])
@token_required
def comprar_revenda(ingresso_id):
    """
    Comprar ingresso em revenda após pagamento MetaMask
    ---
    tags:
      - Ingressos
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: ingresso_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [tx_hash, carteira_comprador]
          properties:
            tx_hash:
              type: string
            carteira_comprador:
              type: string
    responses:
      200:
        description: Revenda concluída
      400:
        description: Erro
      403:
        description: Apenas clientes podem comprar
      404:
        description: Ingresso não encontrado ou não está à venda
    """
    if request.usuario_tipo != TipoUsuario.CLIENTE:
        return jsonify({'erro': 'Apenas clientes podem comprar ingressos'}), 403

    db = SessionLocal()
    try:
        data = request.get_json() or {}
        tx_hash = data.get('tx_hash')
        carteira = data.get('carteira_comprador')

        if not tx_hash or not carteira:
            return jsonify({'erro': 'tx_hash e carteira_comprador são obrigatórios'}), 400

        ingresso = db.query(Ingresso).filter(Ingresso.id == ingresso_id).first()
        if not ingresso:
            return jsonify({'erro': 'Ingresso não encontrado'}), 404
        if ingresso.status != 'a_venda':
            return jsonify({'erro': 'Ingresso não está disponível para revenda'}), 400

        ingresso.id_cliente = request.usuario_id
        ingresso.status = 'ativo'
        ingresso.carteira_comprador = carteira
        ingresso.tx_hash = tx_hash
        ingresso.resale_price_wei = None
        db.commit()

        return jsonify({
            'mensagem': 'Revenda concluída com sucesso',
            'ingresso_id': ingresso.id,
            'token_id': ingresso.token_id,
            'tx_hash': tx_hash,
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== POST - REGISTRAR MINT BLOCKCHAIN ========================
@ingressos_bp.route('/registrar-mint', methods=['POST'])
@token_required
def registrar_mint():
    """
    Registra um mint feito pelo frontend via MetaMask
    ---
    tags:
      - Ingressos
    summary: Registrar mint de NFT
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
          required: [id_evento, token_id, tx_hash, carteira_comprador]
          properties:
            id_evento:
              type: integer
              example: 1
            token_id:
              type: integer
              example: 42
            tx_hash:
              type: string
              example: "0xabc123..."
            carteira_comprador:
              type: string
              example: "0xDEF456..."
    responses:
      201:
        description: Mint registrado com sucesso
      400:
        description: Campos obrigatórios faltando
      404:
        description: Evento não encontrado
    """
    db = SessionLocal()
    try:
        data = request.get_json()
        id_cliente = request.usuario_id

        campos = ['id_evento', 'token_id', 'tx_hash', 'carteira_comprador']
        if not all(data.get(c) is not None for c in campos):
            return jsonify({'erro': f'Campos obrigatórios: {campos}'}), 400

        evento = db.query(Evento).filter(Evento.id == data['id_evento']).first()
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        ingresso = Ingresso(
            id_evento=data['id_evento'],
            id_cliente=id_cliente,
            status='ativo',
            token_id=data['token_id'],
            tx_hash=data['tx_hash'],
            carteira_comprador=data['carteira_comprador'],
        )
        db.add(ingresso)
        db.commit()

        return jsonify({
            'mensagem': 'Mint registrado com sucesso',
            'ingresso_id': ingresso.id,
            'token_id': ingresso.token_id,
            'tx_hash': ingresso.tx_hash,
        }), 201

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
#             func.sum(Compra.quantidade_ingressos),
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