from app.models.usuario import Usuario, TipoUsuario
from app.models.endereco import Endereco
from app.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class UsuarioCliente(Usuario):
    __tablename__ = "usuarios_clientes"

    id = Column(Integer, ForeignKey('usuarios.id'), primary_key=True)
    telefone = Column(String(20), nullable=False)
    acesso_ethereum = Column(String(255), nullable=False)
    endereco_id = Column(Integer, ForeignKey('enderecos.id'))

    endereco = relationship("Endereco", backref="usuario_cliente")

    __mapper_args__ = {
        'polymorphic_identity': TipoUsuario.CLIENTE,
    }

    def __init__(self, id: int, nome: str, cpf: str, email: str, senha: str,
                 endereco: Endereco, telefone: str, acesso_ethereum: str):
        super().__init__(id, nome, cpf, email, senha, TipoUsuario.CLIENTE)
        self.endereco = endereco
        self.telefone = telefone
        self.acesso_ethereum = acesso_ethereum

    def listar_ingressos(self, id_cliente: int):
        pass

    def cadastrar(self):
        pass

    def excluir(self):
        pass

    def alterar(self):
        pass