from app.database import Base
from sqlalchemy import Column, Integer, String
from app.services.cryptography import encrypt_data_aes, decrypt_data_aes

# Exclusivo de CLIENTE
class Endereco(Base):
    __tablename__ = "enderecos"

    id = Column(Integer, primary_key=True, index=True)
    _rua = Column("rua", String(512), nullable=False)
    _cidade = Column("cidade", String(512), nullable=False)
    _estado = Column("estado", String(512), nullable=False)
    _numero = Column("numero", String(512), nullable=False)
    _cep = Column("cep", String(512), nullable=False)

    @property
    def rua(self):
        return decrypt_data_aes(self._rua)

    @rua.setter
    def rua(self, value):
        self._rua = encrypt_data_aes(value)

    @property
    def cidade(self):
        return decrypt_data_aes(self._cidade)

    @cidade.setter
    def cidade(self, value):
        self._cidade = encrypt_data_aes(value)

    @property
    def estado(self):
        return decrypt_data_aes(self._estado)

    @estado.setter
    def estado(self, value):
        self._estado = encrypt_data_aes(value)

    @property
    def numero(self):
        valor = decrypt_data_aes(self._numero)
        return int(valor) if valor is not None else None

    @numero.setter
    def numero(self, value):
        self._numero = encrypt_data_aes(str(value))

    @property
    def cep(self):
        return decrypt_data_aes(self._cep)

    @cep.setter
    def cep(self, value):
        self._cep = encrypt_data_aes(value)

    def __init__(self, rua: str, cidade: str, estado: str, numero: int, cep: str):
        self.rua = rua
        self.cidade = cidade
        self.estado = estado
        self.numero = numero
        self.cep = cep