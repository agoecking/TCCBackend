from app.database import Base
from sqlalchemy import Column, Integer, String

# Exclusivo de CLIENTE
class Endereco(Base):
    __tablename__ = "enderecos"

    id = Column(Integer, primary_key=True, index=True)
    rua = Column(String(255), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    numero = Column(Integer, nullable=False)
    cep = Column(String(8), nullable=False)
    # usuario_cliente_id removido — FK redundante.
    # O relacionamento já é feito por UsuarioCliente.endereco_id → enderecos.id

    def __init__(self, rua: str, cidade: str, estado: str, numero: int, cep: str):
        self.rua = rua
        self.cidade = cidade
        self.estado = estado
        self.numero = numero
        self.cep = cep