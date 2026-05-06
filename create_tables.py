from app.database import Base, engine

from app.models.usuario import Usuario
from app.models.usuario_cliente import UsuarioCliente
from app.models.usuario_organizacao import UsuarioOrganizacao
from app.models.endereco import Endereco
from app.models.organizacao import Organizacao
from app.models.evento import Evento
from app.models.ingresso import Ingresso
from app.models.compra import Compra

Base.metadata.create_all(bind=engine)
print("✅ Tabelas criadas com sucesso!")