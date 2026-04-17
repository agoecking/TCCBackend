from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.compra import Compra
from app.repositories.crud_repository import CrudRepository

class CompraRepository(CrudRepository):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Compra)

    def list_by_cliente(self, id_cliente: int) -> list[Compra]:
        return self.db.query(Compra).filter(Compra.id_cliente == id_cliente).all()

    def list_by_evento(self, id_evento: int) -> list[Compra]:
        return self.db.query(Compra).filter(Compra.id_evento == id_evento).all()

    def total_vendido_por_evento(self, id_evento: int) -> int:
        total = (
            self.db.query(Compra)
            .filter(Compra.id_evento == id_evento)
            .with_entities(self.db.func.sum(Compra.quantidade_ingressos))
            .scalar()
        )
        return total or 0