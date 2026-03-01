from app.models.compra import Compra
from app.repositories.evento_repository import EventoRepository
from app.extensions import db

class TransacaoService:

    @staticmethod
    def pagamento(id_cliente, id_evento, quantidade):

        evento = EventoRepository.buscar_por_id(id_evento)

        if not evento:
            raise ValueError("Evento não encontrado")

        if evento.quantidade_ingressos < quantidade:
            raise ValueError("Ingressos insuficientes")

        evento.quantidade_ingressos -= quantidade

        compra = Compra(
            id_cliente=id_cliente,
            id_evento=id_evento,
            quantidade_ingressos=quantidade
        )

        db.session.add(compra)
        db.session.commit()

        return compra