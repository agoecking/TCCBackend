from sqlalchemy.orm import Session

from app.services.errors import ValidationError, NotFoundError
from app.repositories.evento_repository import EventoRepository
from app.repositories.compra_repository import CompraRepository
from app.repositories.ingresso_repository import IngressoRepository


class IngressoService:
    def __init__(
        self,
        db: Session,
        evento_repo: EventoRepository,
        compra_repo: CompraRepository,
        ingresso_repo: IngressoRepository,
    ):
        self.db = db
        self.evento_repo = evento_repo
        self.compra_repo = compra_repo
        self.ingresso_repo = ingresso_repo

    def comprar_ingressos(self, *, id_cliente: int, id_evento: int, quantidade: int) -> dict:
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
        compra = self.compra_repo.create(
            id_cliente=id_cliente,
            id_evento=evento.id,
            quantidade=quantidade,
        )

        ingressos = self.ingresso_repo.create_many_for_evento(
            evento_id=evento.id,
            quantidade=quantidade,
        )

        # 1 commit no final (atômico)
        self.db.commit()

        # refresh para garantir IDs preenchidos
        self.db.refresh(compra)
        for ing in ingressos:
            self.db.refresh(ing)

        return {
            "id_compra": compra.id,
            "evento_nome": evento.nome,
            "quantidade": quantidade,
            "ingressos_ids": [i.id for i in ingressos],
        }