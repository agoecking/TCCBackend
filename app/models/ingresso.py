from app.database import Base
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship


class Ingresso(Base):
    __tablename__ = "ingressos"

    id = Column(Integer, primary_key=True, index=True)
    id_evento = Column(Integer, ForeignKey('eventos.id'), nullable=False)
    id_cliente = Column(Integer, ForeignKey('usuarios_clientes.id'), nullable=True)
    status = Column(String(50), default="disponivel")

    evento = relationship("Evento", back_populates="ingressos")
    cliente = relationship("UsuarioCliente", backref="ingressos", foreign_keys=[id_cliente])

    def __init__(self, id_evento: int, id_cliente: int = None, status: str = "disponivel"):
        self.id_evento = id_evento
        self.id_cliente = id_cliente
        self.status = status