from app.database import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship


class Compra(Base):
    __tablename__ = "compras"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('usuarios_clientes.id'), nullable=False)
    quantidade_ingressos = Column(Integer, nullable=False)
    id_evento = Column(Integer, ForeignKey('eventos.id'), nullable=False)

    cliente = relationship("UsuarioCliente", backref="compras")
    evento = relationship("Evento", backref="compras")

    def __init__(self, id: int, id_cliente: int, quantidade_ingressos: int, id_evento: int):
        self.id = id
        self.id_cliente = id_cliente
        self.quantidade_ingressos = quantidade_ingressos
        self.id_evento = id_evento