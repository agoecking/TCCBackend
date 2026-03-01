from app.extensions import db

class Evento(db.Model):
    __tablename__ = "eventos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    quantidade_ingressos = db.Column(db.Integer, nullable=False)

    id_organizacao = db.Column(
        db.Integer,
        db.ForeignKey("organizacoes.id"),
        nullable=False
    )