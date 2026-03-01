from app.extensions import db

class Ingresso(db.Model):
    __tablename__ = 'ingressos'
    id = db.Column(db.Integer, primary_key=True)

    id_evento = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)