from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.ingresso import Ingresso
from app.repositories.crud_repository import CrudRepository

class IngressoRepository(CrudRepository):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Ingresso)

    def list_by_evento(self, id_evento: int) -> list[Ingresso]:
        return self.db.query(Ingresso).filter(Ingresso.id_evento == id_evento).all()

    def create_many_for_evento(self, id_evento: int, quantidade: int) -> list[Ingresso]:
        ingressos = [Ingresso(id=None, id_evento=id_evento) for _ in range(quantidade)]
        self.db.add_all(ingressos)
        return ingressos