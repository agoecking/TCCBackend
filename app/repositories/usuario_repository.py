class UsuarioRepository:

    def __init__(self):
        self.usuarios = []

    def salvar(self, usuario):
        self.usuarios.append(usuario)
        return usuario

    def buscar(self, usuario_id):
        for usuario in self.usuarios:
            if usuario.id == usuario_id:
                return usuario
        return None

    def alterar(self, usuario):
        for i, u in enumerate(self.usuarios):
            if u.id == usuario.id:
                self.usuarios[i] = usuario
                return usuario
        return None

    def excluir(self, usuario_id):
        for i, u in enumerate(self.usuarios):
            if u.id == usuario_id:
                del self.usuarios[i]
                return True
        return False