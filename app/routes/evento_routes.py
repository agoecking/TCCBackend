from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.evento import Evento
from app.models.usuario import TipoUsuario, Usuario
from app.models.usuario_organizacao import UsuarioOrganizacao
from app.routes.auth_routes import token_required
from app.repositories.evento_repository import EventoRepository
from app.services.transacao import TransacaoService

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
            'data_hora': e.data_hora,
            'descricao_evento': e.descricao_evento,
            'local_evento': e.local_evento,
            'id_organizacao': e.id_organizacao,
            'id_usuario': e.id_usuario,
            'blockchain_event_id': e.blockchain_event_id,
            'ticket_price_wei': e.ticket_price_wei,
            'max_resale_price_wei': e.max_resale_price_wei,
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
    description: |
      Cria um evento para a organização do usuário autenticado.
      Se ticket_price_wei for informado, o evento também é criado no contrato
      KoynTicket na Sepolia e blockchain_event_id é salvo automaticamente.
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
          required: [nome, quantidade_ingressos]
          properties:
            nome:
              type: string
              example: "Show do Metallica 2027"
            quantidade_ingressos:
              type: integer
              example: 100
            data_hora:
              type: string
              format: date-time
              example: "2027-08-08T12:12:12"
            local_evento:
              type: string
              example: "Curitiba"
            descricao_evento:
              type: string
              example: "Maior show do ano"
            ticket_price_wei:
              type: integer
              example: 1000000000000000
              description: "Preço em wei (obrigatório para criar no blockchain)"
            max_resale_price_wei:
              type: integer
              example: 0
              description: "Teto de revenda em wei. 0 = sem limite."
            royalty_bps:
              type: integer
              example: 1000
              description: "Royalty do organizador em basis points (1000 = 10%)"
    responses:
      201:
        description: Evento criado (com blockchain_event_id se ticket_price_wei informado)
      400:
        description: Campos obrigatórios faltando ou erro ao salvar
      401:
        description: Token não fornecido ou inválido
      403:
        description: Apenas ORGANIZAÇÃO pode criar evento
      404:
        description: Usuário de organização não encontrado
    """
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode criar evento'}), 403

    db = SessionLocal()
    try:
        data = request.get_json() or {}

        required = ['nome', 'quantidade_ingressos']
        if not all(k in data for k in required):
            return jsonify({'erro': 'Campos obrigatórios faltando'}), 400

        usuario = db.query(UsuarioOrganizacao).filter(
            UsuarioOrganizacao.id == request.usuario_id
        ).first()

        if not usuario:
            return jsonify({'erro': 'Usuário de organização não encontrado'}), 404

        repo = EventoRepository(db)
        ticket_price_wei = data.get('ticket_price_wei')
        max_resale_price_wei = data.get('max_resale_price_wei')

        # ── Verificar duplicata confirmada na chain ───────────────────────────
        duplicata = db.query(Evento).filter(
            Evento.nome == data['nome'],
            Evento.id_organizacao == usuario.organizacao_id,
            Evento.blockchain_event_id.isnot(None)
        ).first()
        if duplicata:
            return jsonify({'erro': f"Já existe um evento com este nome registrado na blockchain (id={duplicata.id})"}), 409

        # ── Verificar órfão: salvo no banco mas sem blockchain_event_id ───────
        orfao = db.query(Evento).filter(
            Evento.nome == data['nome'],
            Evento.id_organizacao == usuario.organizacao_id,
            Evento.blockchain_event_id.is_(None)
        ).first()

        if orfao and ticket_price_wei is not None:
            # Tentar registrar o órfão na chain em vez de criar novo registro
            try:
                transacao_svc = TransacaoService()
                _max_resale = int(max_resale_price_wei) if max_resale_price_wei is not None else 0
                blockchain_event_id = transacao_svc.criar_evento_blockchain(
                    nome=orfao.nome,
                    ticket_price_wei=int(ticket_price_wei),
                    max_tickets=orfao.quantidade_ingressos,
                    max_resale_price_wei=_max_resale,
                    royalty_bps=int(data.get('royalty_bps', 1000)),
                    organizer_address=usuario.organizacao.carteira_ethereum or None,
                )
                orfao.blockchain_event_id = blockchain_event_id

                # Sincroniza DB com os valores reais da chain (fonte de verdade)
                try:
                    info = transacao_svc.info_evento_blockchain(blockchain_event_id)
                    orfao.ticket_price_wei      = str(info['ticket_price_wei'])
                    orfao.max_resale_price_wei  = str(info['max_resale_price_wei'])
                except Exception:
                    orfao.ticket_price_wei      = str(ticket_price_wei)
                    orfao.max_resale_price_wei  = str(_max_resale)

                db.commit()
                db.refresh(orfao)
            except Exception as e:
                return jsonify({'erro': f'Falha ao registrar evento pendente na blockchain: {str(e)}'}), 500

            return jsonify({
                'id': orfao.id,
                'nome': orfao.nome,
                'quantidade_ingressos': orfao.quantidade_ingressos,
                'data_hora': orfao.data_hora,
                'local_evento': orfao.local_evento,
                'descricao_evento': orfao.descricao_evento,
                'id_organizacao': orfao.id_organizacao,
                'id_usuario': orfao.id_usuario,
                'blockchain_event_id': orfao.blockchain_event_id,
                'ticket_price_wei': orfao.ticket_price_wei,
                'max_resale_price_wei': orfao.max_resale_price_wei,
                'recuperado': True,
            }), 201

        # ── Criação normal ────────────────────────────────────────────────────
        evento = Evento(
            id=None,
            nome=data['nome'],
            quantidade_ingressos=data['quantidade_ingressos'],
            data_hora=data.get('data_hora'),
            local_evento=data.get('local_evento'),
            descricao_evento=data.get('descricao_evento'),
            id_organizacao=usuario.organizacao_id,
            id_usuario=usuario.id,
            ticket_price_wei=str(ticket_price_wei) if ticket_price_wei is not None else None,
            max_resale_price_wei=str(max_resale_price_wei) if max_resale_price_wei is not None else None,
        )

        repo.create(evento)
        db.commit()
        db.refresh(evento)

        # ── Registrar no contrato KoynTicket ──────────────────────────────────
        if ticket_price_wei is not None:
            try:
                transacao_svc = TransacaoService()
                _max_resale = int(max_resale_price_wei) if max_resale_price_wei is not None else 0
                blockchain_event_id = transacao_svc.criar_evento_blockchain(
                    nome=data['nome'],
                    ticket_price_wei=int(ticket_price_wei),
                    max_tickets=data['quantidade_ingressos'],
                    max_resale_price_wei=_max_resale,
                    royalty_bps=int(data.get('royalty_bps', 1000)),
                    organizer_address=usuario.organizacao.carteira_ethereum or None,
                )
                evento.blockchain_event_id = blockchain_event_id

                # Sincroniza DB com os valores reais da chain (fonte de verdade)
                try:
                    info = transacao_svc.info_evento_blockchain(blockchain_event_id)
                    evento.ticket_price_wei     = str(info['ticket_price_wei'])
                    evento.max_resale_price_wei = str(info['max_resale_price_wei'])
                except Exception:
                    pass  # mantém os valores digitados se a leitura falhar

                db.commit()
            except Exception as e:
                import traceback
                print(f"[Blockchain] ERRO ao registrar evento id={evento.id} no contrato: {e}")
                print(traceback.format_exc())

        if ticket_price_wei is not None and evento.blockchain_event_id is None:
            return jsonify({
                'erro': 'Evento salvo no banco mas falhou ao registrar na blockchain. Tente criar o evento novamente com o mesmo nome para recuperar o registro.',
                'id': evento.id,
            }), 500

        return jsonify({
            'id': evento.id,
            'nome': evento.nome,
            'quantidade_ingressos': evento.quantidade_ingressos,
            'data_hora': evento.data_hora,
            'local_evento': evento.local_evento,
            'descricao_evento': evento.descricao_evento,
            'id_organizacao': evento.id_organizacao,
            'id_usuario': evento.id_usuario,
            'blockchain_event_id': evento.blockchain_event_id,
            'ticket_price_wei': evento.ticket_price_wei,
            'max_resale_price_wei': evento.max_resale_price_wei,
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
        evento = repo.get_by_id(id)

        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        return jsonify({
            'id': evento.id,
            'nome': evento.nome,
            'quantidade_ingressos': evento.quantidade_ingressos,
            'data_hora': evento.data_hora,
            'local_evento': evento.local_evento,
            'descricao_evento': evento.descricao_evento,
            'id_organizacao': evento.id_organizacao,
            'blockchain_event_id': evento.blockchain_event_id,
            'ticket_price_wei': evento.ticket_price_wei,
            'max_resale_price_wei': evento.max_resale_price_wei,
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
    description: Atualiza um evento pertencente à organização do usuário autenticado.
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
    responses:
      200:
        description: Evento atualizado com sucesso
      400:
        description: Erro
      401:
        description: Token não fornecido ou inválido
      403:
        description: Apenas ORGANIZAÇÃO pode atualizar evento ou evento pertence a outra organização
      404:
        description: Usuário de organização não encontrado ou evento não encontrado
    """
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode atualizar evento'}), 403

    db = SessionLocal()
    try:
        usuario = db.query(UsuarioOrganizacao).filter(
            UsuarioOrganizacao.id == request.usuario_id
        ).first()

        if not usuario:
            return jsonify({'erro': 'Usuário de organização não encontrado'}), 404

        repo = EventoRepository(db)
        evento = repo.get_by_id(id)

        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        if evento.id_organizacao != usuario.organizacao_id:
            return jsonify({'erro': 'Você não pode alterar eventos de outra organização'}), 403

        data = request.get_json() or {}

        if 'nome' in data:
            evento.nome = data['nome']
        if 'quantidade_ingressos' in data:
            evento.quantidade_ingressos = data['quantidade_ingressos']
        if 'descricao_evento' in data:
            evento.descricao_evento = data['descricao_evento']
        if 'local_evento' in data:
            evento.local_evento = data['local_evento']
        if 'data_hora' in data:
            evento.data_hora = data['data_hora']

        db.commit()
        db.refresh(evento)

        return jsonify({
            'id': evento.id,
            'nome': evento.nome,
            'quantidade_ingressos': evento.quantidade_ingressos,
            'descricao_evento': evento.descricao_evento,
            'local_evento': evento.local_evento,
            'data_hora': evento.data_hora,
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
    description: Remove um evento pertencente à organização do usuário autenticado.
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
        description: Evento deletado com sucesso
      400:
        description: Erro
      401:
        description: Token não fornecido ou inválido
      403:
        description: Apenas ORGANIZAÇÃO pode deletar evento ou evento pertence a outra organização
      404:
        description: Usuário de organização não encontrado ou evento não encontrado
    """
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode deletar evento'}), 403

    db = SessionLocal()
    try:
        usuario = db.query(UsuarioOrganizacao).filter(
            UsuarioOrganizacao.id == request.usuario_id
        ).first()

        if not usuario:
            return jsonify({'erro': 'Usuário de organização não encontrado'}), 404

        repo = EventoRepository(db)
        evento = repo.get_by_id(id)

        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        if evento.id_organizacao != usuario.organizacao_id:
            return jsonify({'erro': 'Você não pode deletar eventos de outra organização'}), 403

        # Desativar on-chain antes de deletar do banco
        if evento.blockchain_event_id is not None:
            try:
                transacao_svc = TransacaoService()
                transacao_svc.desativar_evento_blockchain(evento.blockchain_event_id)
            except Exception as e:
                print(f"[Blockchain] Aviso: falha ao desativar evento {evento.blockchain_event_id} on-chain: {e}")
                # Não bloqueia a deleção do banco

        repo.delete(evento)
        db.commit()

        return jsonify({'mensagem': 'Evento deletado com sucesso'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


@eventos_bp.route('/<int:id>/sync-chain', methods=['POST'])
@token_required
def sync_evento_chain(id):
    """
    Sincroniza os dados do evento com os valores reais da blockchain
    ---
    tags:
      - Eventos
    summary: Sincronizar evento com blockchain
    description: |
      Lê os valores reais de ticket_price_wei e max_resale_price_wei direto
      do contrato KoynTicket e atualiza o banco de dados.
      Útil quando o DB ficou desincronizado da chain por erros de criação.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Evento sincronizado com sucesso
      404:
        description: Evento não encontrado ou sem blockchain_event_id
      403:
        description: Sem permissão
    """
    if request.usuario_tipo != TipoUsuario.ORGANIZACAO:
        return jsonify({'erro': 'Apenas ORGANIZAÇÃO pode sincronizar eventos'}), 403

    db = SessionLocal()
    try:
        usuario = db.query(UsuarioOrganizacao).filter(
            UsuarioOrganizacao.id == request.usuario_id
        ).first()
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        repo = EventoRepository(db)
        evento = repo.get_by_id(id)
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404
        if evento.id_organizacao != usuario.organizacao_id:
            return jsonify({'erro': 'Sem permissão para este evento'}), 403
        if evento.blockchain_event_id is None:
            return jsonify({'erro': 'Evento sem blockchain_event_id — não é possível sincronizar'}), 404

        transacao_svc = TransacaoService()
        info = transacao_svc.info_evento_blockchain(evento.blockchain_event_id)

        evento.ticket_price_wei     = str(info['ticket_price_wei'])
        evento.max_resale_price_wei = str(info['max_resale_price_wei'])
        db.commit()

        return jsonify({
            'mensagem': 'Evento sincronizado com a blockchain',
            'blockchain_event_id': evento.blockchain_event_id,
            'ticket_price_wei': evento.ticket_price_wei,
            'max_resale_price_wei': evento.max_resale_price_wei,
            'ticket_price_eth': round(info['ticket_price_wei'] / 1e18, 6),
            'max_resale_price_eth': round(info['max_resale_price_wei'] / 1e18, 6),
            'organizer': info['organizer'],
            'active': info['active'],
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()