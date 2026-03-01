from app.extensions import db

class Compra(db.Model):
    __tablename__ = "compras"

    id = db.Column(db.Integer, primary_key=True)
    quantidade_ingressos = db.Column(db.Integer, nullable=False)

    id_cliente = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    id_evento = db.Column(
        db.Integer,
        db.ForeignKey("eventos.id"),
        nullable=False
    )