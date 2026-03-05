from app.database import Base, engine
from app.models.usuario import Usuario
from app.models.usuario_cliente import UsuarioCliente
from app.models.endereco import Endereco

# Criar todas as tabelas
Base.metadata.create_all(bind=engine)
print("✅ Tabelas criadas com sucesso!")