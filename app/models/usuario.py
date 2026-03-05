from abc import ABC
from app.interfaces.icrud import ICrud
from app.database import Base
from sqlalchemy import Column, Integer, String, Enum
import enum


class TipoUsuario(str, enum.Enum):
    CLIENTE = "cliente"
    ORGANIZACAO = "organizacao"


class Usuario(Base, ABC, ICrud):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)
    tipo_usuario = Column(Enum(TipoUsuario), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
        'polymorphic_on': tipo_usuario
    }

    def __init__(self, id: int, nome: str, cpf: str, email: str, senha: str, tipo_usuario: str):
        self.id = id
        self.nome = nome
        self.cpf = cpf
        self.email = email
        self.senha = senha
        self.tipo_usuario = tipo_usuario

    def cadastrar(self):
        raise NotImplementedError("cadastrar() não implementado")

    def excluir(self):
        raise NotImplementedError("excluir() não implementado")

    def alterar(self):
        raise NotImplementedError("alterar() não implementado")