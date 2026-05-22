from sqlalchemy.orm import Session

from app.services.errors import ValidationError, NotFoundError
from app.services.transacao import TransacaoService
from app.repositories.evento_repository import EventoRepository
from app.repositories.compra_repository import CompraRepository
from app.repositories.ingresso_repository import IngressoRepository
from app.models.compra import Compra
from app.models.ingresso import Ingresso


class IngressoService:
    def __init__(
        self,
        db: Session,
        evento_repo: EventoRepository,
        compra_repo: CompraRepository,
        ingresso_repo: IngressoRepository,
        transacao_service: TransacaoService = None,
    ):
        self.db = db
        self.evento_repo = evento_repo
        self.compra_repo = compra_repo
        self.ingresso_repo = ingresso_repo
        self.transacao_service = transacao_service

    def comprar_ingressos(self, *, id_cliente: int, id_evento: int, quantidade: int,
                          carteira_comprador: str = None, token_uri: str = "") -> dict:
        # -------- validações de entrada --------
        if not id_evento:
            raise ValidationError("id_evento é obrigatório")
        if not quantidade:
            raise ValidationError("quantidade é obrigatória")
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValidationError("quantidade deve ser um inteiro > 0")

        # -------- buscar evento --------
        evento = self.evento_repo.get_by_id(id_evento)
        if not evento:
            raise NotFoundError("Evento não encontrado")

        # -------- regra de disponibilidade --------
        vendidos = self.compra_repo.total_vendido_por_evento(evento.id)
        disponiveis = evento.quantidade_ingressos - vendidos

        if quantidade > disponiveis:
            raise ValidationError(f"Quantidade insuficiente. Disponíveis: {disponiveis}")

        # -------- persistência (transação) --------
        compra = Compra(
            id=None,
            id_cliente=id_cliente,
            id_evento=evento.id,
            quantidade_ingressos=quantidade,
        )
        self.compra_repo.create(compra)

        ingressos = []
        for _ in range(quantidade):
            ingresso = Ingresso(
                id_evento=evento.id,
                id_cliente=id_cliente,
                status="disponivel",
            )
            self.ingresso_repo.create(ingresso)
            ingressos.append(ingresso)

        # 1 commit no final (atômico)
        self.db.commit()

        # refresh para garantir IDs preenchidos
        self.db.refresh(compra)
        for ing in ingressos:
            self.db.refresh(ing)

        # ── Mint NFTs no blockchain (se evento tiver blockchain_event_id) ──
        if self.transacao_service and evento.blockchain_event_id is not None:
            for ing in ingressos:
                try:
                    resultado = self.transacao_service.mint_nft(
                        blockchain_event_id=evento.blockchain_event_id,
                        token_uri=token_uri,
                    )
                    ing.token_id           = resultado["token_id"]
                    ing.tx_hash            = resultado["tx_hash"]
                    ing.carteira_comprador = carteira_comprador
                except Exception as e:
                    # Falha no blockchain não reverte a compra off-chain
                    ing.status = "pendente_blockchain"
                    print(f"[Blockchain] Erro ao mintar ingresso {ing.id}: {e}")

            self.db.commit()
            for ing in ingressos:
                self.db.refresh(ing)

        return {
            "id_compra":    compra.id,
            "evento_nome":  evento.nome,
            "quantidade":   quantidade,
            "ingressos_ids": [i.id for i in ingressos],
            "tokens_ids":   [i.token_id for i in ingressos],
            "tx_hashes":    [i.tx_hash for i in ingressos],
        }

    def transferir_ingresso(self, id_ingresso: int, id_dono_atual: int, id_novo_dono: int):
        """Altera a propriedade de um ingresso"""
        ingresso = self.db.query(Ingresso).filter(Ingresso.id == id_ingresso).first()
        if not ingresso:
            raise NotFoundError("Ingresso não encontrado")
            
        if ingresso.id_cliente != id_dono_atual:
            raise ValidationError("Você não é dono deste ingresso para poder transferir.")
            
        if ingresso.status == "a_venda":
            raise ValidationError("Ingressos apontados como a venda não podem ser transferidos diretamente.")
            
        ingresso.id_cliente = id_novo_dono
        self.db.commit()
        return ingresso

    def anunciar_revenda(self, id_ingresso: int, id_dono: int):
        """Muda o status do ingresso que você é dono para a_venda no mercado"""
        ingresso = self.db.query(Ingresso).filter(Ingresso.id == id_ingresso).first()
        if not ingresso or ingresso.id_cliente != id_dono:
            raise ValidationError("Só o dono real pode anunciar a revenda deste bilhete.")
            
        if ingresso.status == "utilizado":
            raise ValidationError("Ingresso já utilizado!")
            
        ingresso.status = "a_venda"
        self.db.commit()
        return ingresso