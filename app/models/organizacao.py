from app.extensions import db

class Organizacao(db.Model):
    __tablename__ = "organizacoes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(18), nullable=False)