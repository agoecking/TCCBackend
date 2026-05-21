from app.models.usuario import Usuario, TipoUsuario
from app.models.endereco import Endereco
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.services.cryptography import encrypt_data_aes, decrypt_data_aes

class UsuarioCliente(Usuario):
    __tablename__ = "usuarios_clientes"

    id = Column(Integer, ForeignKey('usuarios.id'), primary_key=True)
    _telefone = Column("telefone", String(512), nullable=False)
    carteira_ethereum = Column(String(255), nullable=True)
    endereco_id = Column(Integer, ForeignKey('enderecos.id'))

    endereco = relationship("Endereco", foreign_keys=[endereco_id], backref="usuario_cliente")
    __mapper_args__ = {
        'polymorphic_identity': TipoUsuario.CLIENTE,
    }

    @property
    def telefone(self):
        return decrypt_data_aes(self._telefone)

    @telefone.setter
    def telefone(self, value):
        self._telefone = encrypt_data_aes(value)

    def __init__(self, nome: str, cpf: str, email: str, senha: str,
                 endereco: Endereco, telefone: str, carteira_ethereum: str = ''):
        super().__init__(nome, cpf, email, senha, TipoUsuario.CLIENTE)
        self.endereco = endereco
        self.telefone = telefone
        self.carteira_ethereum = carteira_ethereum