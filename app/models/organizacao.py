from app.database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class Organizacao(Base):
    __tablename__ = "organizacoes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    # nullable=True — carteira não é exigida no cadastro; salva automaticamente via Navbar (igual ao cliente)
    carteira_ethereum = Column('acesso_ethereum', String(255), nullable=True)

    eventos = relationship("Evento", back_populates="organizacao")
    usuarios_organizacao = relationship("UsuarioOrganizacao", back_populates="organizacao")

    def __init__(self, id: int, nome: str, cnpj: str, carteira_ethereum: str = None):
        self.id = id
        self.nome = nome
        self.cnpj = cnpj
        self.carteira_ethereum = carteira_ethereum
