from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.evento import Evento
from app.repositories.crud_repository import CrudRepository

class EventoRepository(CrudRepository):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Evento)

    def list_all(self) -> list[Evento]:
        return self.db.query(Evento).all()

    def list_by_organizacao(self, id_organizacao: int) -> list[Evento]:
        return self.db.query(Evento).filter(Evento.id_organizacao == id_organizacao).all()