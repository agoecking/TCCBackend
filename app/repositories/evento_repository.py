class EventoRepository:

    def __init__(self):
        self.eventos = []

    def salvar(self, evento):
        self.eventos.append(evento)
        return evento

    def buscar(self, evento_id):
        for evento in self.eventos:
            if evento.id == evento_id:
                return evento
        return None

    def alterar(self, evento):
        for i, e in enumerate(self.eventos):
            if e.id == evento.id:
                self.eventos[i] = evento
                return evento
        return None

    def excluir(self, evento_id):
        for i, e in enumerate(self.eventos):
            if e.id == evento_id:
                del self.eventos[i]
                return True
        return False