from sqlalchemy.orm import Session
from app.models.usuario_cliente import UsuarioCliente
from app.models.endereco import Endereco


class UsuarioRepository:

    @staticmethod
    def salvar(usuario: UsuarioCliente, db_session: Session):
        """Salva um novo usuário cliente no banco"""
        db_session.add(usuario)
        db_session.commit()
        db_session.refresh(usuario)
        return usuario

    @staticmethod
    def buscar_por_email(email: str, db_session: Session):
        """Busca usuário por email"""
        return db_session.query(UsuarioCliente).filter(
            UsuarioCliente.email == email
        ).first()

    @staticmethod
    def buscar_por_cpf(cpf: str, db_session: Session):
        """Busca usuário por CPF"""
        return db_session.query(UsuarioCliente).filter(
            UsuarioCliente.cpf == cpf
        ).first()