from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.organizacao import Organizacao
from app.repositories.crud_repository import CrudRepository

class OrganizacaoRepository(CrudRepository):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Organizacao)

    def list_all(self) -> list[Organizacao]:
        return self.db.query(Organizacao).all()

    def get_by_cnpj(self, cnpj: str) -> Organizacao | None:
        return self.db.query(Organizacao).filter(Organizacao.cnpj == cnpj).first()