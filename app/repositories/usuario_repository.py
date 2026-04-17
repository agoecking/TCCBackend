from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.usuario_cliente import UsuarioCliente
from app.repositories.crud_repository import CrudRepository

class UsuarioClienteRepository(CrudRepository):
    def __init__(self, db: Session):
        super().__init__(db=db, model=UsuarioCliente)

    def list_all(self) -> list[UsuarioCliente]:
        return self.db.query(UsuarioCliente).all()

    def get_by_email(self, email: str) -> UsuarioCliente | None:
        return self.db.query(UsuarioCliente).filter(UsuarioCliente.email == email).first()

    def get_by_cpf(self, cpf: str) -> UsuarioCliente | None:
        return self.db.query(UsuarioCliente).filter(UsuarioCliente.cpf == cpf).first()