from app.database import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship


class Ingresso(Base):
    __tablename__ = "ingressos"

    id = Column(Integer, primary_key=True, index=True)
    id_evento = Column(Integer, ForeignKey('eventos.id'), nullable=False)

    evento = relationship("Evento", back_populates="ingressos")

    def __init__(self, id: int, id_evento: int):
        self.id = id
        self.id_evento = id_evento

    def smart_contract(self):
        pass

    def cadastrar(self):
        pass

    def excluir(self):
        pass

    def alterar(self):
        pass