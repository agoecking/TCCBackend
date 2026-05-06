from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.usuario import Usuario, TipoUsuario


class UsuarioOrganizacao(Usuario):
    __tablename__ = "usuarios_organizacao"

    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    organizacao_id = Column(Integer, ForeignKey("organizacoes.id"), nullable=False)

    organizacao = relationship("Organizacao", back_populates="usuarios_organizacao")

    __mapper_args__ = {
        "polymorphic_identity": TipoUsuario.ORGANIZACAO,
    }

    def __init__(self, nome: str, cpf: str, email: str, senha: str, organizacao_id: int):
        super().__init__(nome, cpf, email, senha, TipoUsuario.ORGANIZACAO)
        self.organizacao_id = organizacao_id