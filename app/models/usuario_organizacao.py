from app.models.usuario import Usuario, TipoUsuario


class UsuarioOrganizacao(Usuario):
    __mapper_args__ = {
        'polymorphic_identity': TipoUsuario.ORGANIZACAO,  # ✅ Adicione isso
    }

    def __init__(self, id: int, nome: str, cpf: str, email: str, senha: str, organizacao_id: int):
        super().__init__(id, nome, cpf, email, senha, TipoUsuario.ORGANIZACAO)
        self.organizacao_id = organizacao_id

    def cadastrar(self):
        print(f"Cadastrando usuário de organização: {self.nome}")
        pass

    def excluir(self):
        print(f"Excluindo usuário de organização: {self.nome}")
        pass

    def alterar(self):
        print(f"Alterando usuário de organização: {self.nome}")
        pass