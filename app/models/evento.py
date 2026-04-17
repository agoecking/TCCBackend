from app.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    quantidade_ingressos = Column(Integer, nullable=False)
    id_organizacao = Column(Integer, ForeignKey('organizacoes.id'), nullable=False)

    organizacao = relationship("Organizacao", back_populates="eventos")
    ingressos = relationship("Ingresso", back_populates="evento")

    def __init__(self, id: int, nome: str, quantidade_ingressos: int, id_organizacao: int):
        self.id = id
        self.nome = nome
        self.quantidade_ingressos = quantidade_ingressos
        self.id_organizacao = id_organizacao

    def criar(self):
        pass

    def gerar_ingressos(self):
        pass

    def cadastrar(self):
        pass

    def excluir(self):
        pass

    def alterar(self):
        pass