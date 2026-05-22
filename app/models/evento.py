from datetime import datetime

from app.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models import Organizacao


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    quantidade_ingressos = Column(Integer, nullable=False)
    id_organizacao = Column(Integer, ForeignKey('organizacoes.id'), nullable=False)
    id_usuario = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    descricao_evento = Column(String(280), nullable=False)
    data_hora = Column(DateTime, nullable=False)
    local_evento = Column(String(280), nullable=False)
    blockchain_event_id = Column(Integer, nullable=True)
    ticket_price_wei = Column(String(32), nullable=True)          # preço em wei como string (evita overflow)
    max_resale_price_wei = Column(String(32), nullable=True)      # teto de revenda em wei (0 ou NULL = sem limite)

    organizacao = relationship("Organizacao", back_populates="eventos")
    ingressos = relationship("Ingresso", back_populates="evento")

    def __init__(self, id: int, nome: str, quantidade_ingressos: int, id_organizacao: int, id_usuario: int, descricao_evento: str, local_evento: str, data_hora: DateTime, ticket_price_wei: str = None, blockchain_event_id: int = None, max_resale_price_wei: str = None):
        self.id = id
        self.nome = nome
        self.quantidade_ingressos = quantidade_ingressos
        self.id_organizacao = id_organizacao
        self.id_usuario = id_usuario
        self.data_hora = data_hora
        self.descricao_evento = descricao_evento
        self.local_evento = local_evento
        self.ticket_price_wei = ticket_price_wei
        self.blockchain_event_id = blockchain_event_id
        self.max_resale_price_wei = max_resale_price_wei