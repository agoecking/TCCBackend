from app.models.usuario import Usuario


class UsuarioOrganizacao(Usuario):

    def __init__(self, id: int, nome: str, cpf: str, email: str, senha: str, organizacao_id: int):
        super().__init__(id, nome, cpf, email, senha, "Organização")
        self.organizacao_id = organizacao_id

    def cadastrar(self):
        print(f"Cadastrando usuário de organização: {self.nome}")
        # Implementar lógica de cadastro
        pass


def excluir(self):
    print(f"Excluindo usuário de organização: {self.nome}")
    # Implementar lógica de exclusão
    pass


def alterar(self):
    print(f"Alterando usuário de organização: {self.nome}")
    # Implementar lógica de alteração
    pass
