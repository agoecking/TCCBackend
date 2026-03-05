from app.database import Base
from app.interfaces.icrud import ICrud
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class Organizacao(Base, ICrud):
    __tablename__ = "organizacoes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    acesso_ethereum = Column(String(255), nullable=False)

    eventos = relationship("Evento", back_populates="organizacao")

    def __init__(self, id: int, nome: str, cnpj: str, acesso_ethereum: str):
        self.id = id
        self.nome = nome
        self.cnpj = cnpj
        self.acesso_ethereum = acesso_ethereum

    def cadastrar(self):
        pass

    def excluir(self):
        pass

    def alterar(self):
        pass