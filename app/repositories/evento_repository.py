from app.models.evento import Evento
from app.extensions import db

class EventoRepository:

    @staticmethod
    def salvar(evento):
        db.session.add(evento)
        db.session.commit()
        return evento

    @staticmethod
    def buscar_por_id(id_evento):
        return Evento.query.get(id_evento)

    @staticmethod
    def listar():
        return Evento.query.all()