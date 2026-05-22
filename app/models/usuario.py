from app.database import Base
from sqlalchemy import Column, Integer, String, Enum
import enum
from app.services.cryptography import encrypt_data_aes, decrypt_data_aes, hash_password_argon2

class TipoUsuario(str, enum.Enum):
    CLIENTE = "cliente"
    ORGANIZACAO = "organizacao"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    _cpf = Column("cpf", String(512), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)
    tipo_usuario = Column(Enum(TipoUsuario), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
        'polymorphic_on': tipo_usuario
    }

    @property
    def cpf(self):
        return decrypt_data_aes(self._cpf)

    @cpf.setter
    def cpf(self, value):
        self._cpf = encrypt_data_aes(value)

    def set_senha(self, senha_plana: str):
        self.senha = hash_password_argon2(senha_plana)

    def __init__(self, nome: str, cpf: str, email: str, senha: str, tipo_usuario: TipoUsuario):
        self.nome = nome
        self.cpf = cpf
        self.email = email
        self.set_senha(senha)
        self.tipo_usuario = tipo_usuario