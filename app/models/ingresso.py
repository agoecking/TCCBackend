from app.database import Base
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship


class Ingresso(Base):
    __tablename__ = "ingressos"

    id = Column(Integer, primary_key=True, index=True)
    id_evento = Column(Integer, ForeignKey('eventos.id'), nullable=False)
    id_cliente = Column(Integer, ForeignKey('usuarios_clientes.id'), nullable=True)
    status = Column(String(50), default="disponivel")

    # Campos blockchain
    token_id = Column(Integer, nullable=True)
    tx_hash = Column(String(66), nullable=True)
    carteira_comprador = Column(String(42), nullable=True)
    resale_price_wei = Column(String(32), nullable=True)

    evento = relationship("Evento", back_populates="ingressos")
    cliente = relationship("UsuarioCliente", backref="ingressos", foreign_keys=[id_cliente])

    def __init__(self, id_evento: int, id_cliente: int = None, status: str = "disponivel",
                 token_id: int = None, tx_hash: str = None, carteira_comprador: str = None,
                 resale_price_wei: str = None):
        self.id_evento = id_evento
        self.id_cliente = id_cliente
        self.status = status
        self.token_id = token_id
        self.tx_hash = tx_hash
        self.carteira_comprador = carteira_comprador
        self.resale_price_wei = resale_price_wei