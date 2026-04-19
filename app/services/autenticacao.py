from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AutenticacaoService:
    """Service para operações de autenticação"""

    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository

    def gerar_hash_senha(self, senha_texto_plano: str) -> str:
        """Pega 'senha123' e a transforma num hash seguro criptografado"""
        return pwd_context.hash(senha_texto_plano)

    def verificar_senha(self, senha_texto_plano: str, senha_hash: str) -> bool:
        """Valida a senha batendo a string com o hash salvo"""
        return pwd_context.verify(senha_texto_plano, senha_hash)

    def login(self, email: str, senha_digitada: str):
        """
        Realiza login de um usuário
        """
        usuario = self.usuario_repository.buscar_por_email(email)
        
        # Se usuário não for encontrado ou a senha não bater com o hash
        if not usuario or not self.verificar_senha(senha_digitada, usuario.senha):
            return None
            
        return usuario

    def validar_acesso(self, usuario_id: int, recurso: str):
        """
        Valida se o usuário tem acesso a um recurso
        """
        # Exemplo simples mantido da sua base original
        usuario = self.usuario_repository.buscar(usuario_id)
        if usuario is None:
            return False
        return True