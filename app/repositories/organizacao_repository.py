class OrganizacaoRepository:

    def __init__(self):
        self.organizacoes = []

    def salvar(self, organizacao):
        self.organizacoes.append(organizacao)
        return organizacao

    def buscar(self, organizacao_id):
        for org in self.organizacoes:
            if org.id == organizacao_id:
                return org
        return None

    def alterar(self, organizacao):
        for i, org in enumerate(self.organizacoes):
            if org.id == organizacao.id:
                self.organizacoes[i] = organizacao
                return organizacao
        return None

    def excluir(self, organizacao_id):
        for i, org in enumerate(self.organizacoes):
            if org.id == organizacao_id:
                del self.organizacoes[i]
                return True
        return False