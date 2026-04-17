from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import SessionLocal
from app.models.usuario import Usuario, TipoUsuario
from app.models.usuario_cliente import UsuarioCliente
from app.models.endereco import Endereco
from app.models.organizacao import Organizacao
import jwt
from datetime import datetime, timedelta
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Chave secreta para JWT (deve estar no .env)
SECRET_KEY = "tccbackend-dev-local-secret-key-fixa"

# ======================== REGISTRAR CLIENTE ========================
@auth_bp.route("/register-cliente", methods=["POST"])
def register_cliente():
    """
    Registrar novo cliente
    ---
    tags:
      - Auth
    summary: Registrar cliente
    description: Cria um usuário do tipo cliente com endereço e senha hasheada.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [nome, cpf, email, senha, telefone, acesso_ethereum, endereco]
          properties:
            nome:
              type: string
              example: "Cliente 1"
            cpf:
              type: string
              example: "12345678900"
            email:
              type: string
              example: "cliente1@email.com"
            senha:
              type: string
              example: "123"
            telefone:
              type: string
              example: "11999999999"
            acesso_ethereum:
              type: string
              example: "0xabc"
            endereco:
              type: object
              required: [rua, numero, cidade, estado, cep]
              properties:
                rua:
                  type: string
                  example: "Rua A"
                numero:
                  type: integer
                  example: 10
                cidade:
                  type: string
                  example: "São Paulo"
                estado:
                  type: string
                  example: "SP"
                cep:
                  type: string
                  example: "01001000"
    responses:
      201:
        description: Cliente registrado
      400:
        description: Erro (campos obrigatórios faltando / falha ao salvar)
      409:
        description: Email ou CPF já registrado
    """
    db = SessionLocal()

    try:
        data = request.get_json()

        # Validações
        required_fields = ['nome', 'cpf', 'email', 'senha', 'telefone', 'acesso_ethereum', 'endereco']
        if not all(field in data for field in required_fields):
            return jsonify({'erro': 'Campos obrigatórios faltando'}), 400

        # Verificar se email já existe
        existing_user = db.query(Usuario).filter(Usuario.email == data['email']).first()
        if existing_user:
            return jsonify({'erro': 'Email já registrado'}), 409

        # Verificar se CPF já existe
        existing_cpf = db.query(Usuario).filter(Usuario.cpf == data['cpf']).first()
        if existing_cpf:
            return jsonify({'erro': 'CPF já registrado'}), 409

        # Criar endereço
        endereco = Endereco(
            rua=data['endereco'].get('rua'),
            numero=data['endereco'].get('numero'),
            cidade=data['endereco'].get('cidade'),
            estado=data['endereco'].get('estado'),
            cep=data['endereco'].get('cep')
        )

        # Criar usuário cliente com senha hasheada
        usuario = UsuarioCliente(
            nome=data['nome'],
            cpf=data['cpf'],
            email=data['email'],
            senha=generate_password_hash(data['senha']),
            telefone=data['telefone'],
            acesso_ethereum=data['acesso_ethereum'],
            endereco=endereco
        )

        db.add(endereco)
        db.add(usuario)
        db.commit()

        return jsonify({
            'mensagem': 'Cliente registrado com sucesso',
            'id': usuario.id,
            'email': usuario.email
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== LOGIN ========================
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login de usuário
    ---
    tags:
      - Auth
    summary: Login
    description: Retorna um JWT válido por 24h.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, senha]
          properties:
            email:
              type: string
              example: "cliente1@email.com"
            senha:
              type: string
              example: "123"
    responses:
      200:
        description: Login realizado
      400:
        description: Email e senha são obrigatórios / erro genérico
      401:
        description: Email ou senha inválidos
    """
    db = SessionLocal()

    try:
        data = request.get_json()

        if not data.get('email') or not data.get('senha'):
            return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

        # Buscar usuário pelo email
        usuario = db.query(Usuario).filter(Usuario.email == data['email']).first()

        if not usuario or not check_password_hash(usuario.senha, data['senha']):
            return jsonify({'erro': 'Email ou senha inválidos'}), 401

        # Gerar JWT token
        token = jwt.encode(
            {
                'id': usuario.id,
                'email': usuario.email,
                'tipo': usuario.tipo_usuario,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            SECRET_KEY,
            algorithm='HS256'
        )

        return jsonify({
            'mensagem': 'Login realizado com sucesso',
            'token': token,
            'usuario': {
                'id': usuario.id,
                'nome': usuario.nome,
                'email': usuario.email,
                'tipo': usuario.tipo_usuario
            }
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== VALIDAR TOKEN ========================
@auth_bp.route("/validate-token", methods=["POST"])
def validate_token():
    """
    Validar token JWT
    ---
    tags:
      - Auth
    summary: Validar token
    security:
      - BearerAuth: []
    parameters:
      - in: header
        name: Authorization
        type: string
        required: true
        description: "Bearer <token>"
    responses:
      200:
        description: Token válido
      401:
        description: Token não fornecido / expirado / inválido
      400:
        description: Erro
    """
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401

        # Remover "Bearer " se existir
        if token.startswith('Bearer '):
            token = token[7:]

        # Validar token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        return jsonify({
            'valido': True,
            'usuario_id': payload['id'],
            'email': payload['email'],
            'tipo': payload['tipo']
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'erro': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'erro': 'Token inválido'}), 401
    except Exception as e:
        return jsonify({'erro': str(e)}), 400


# ======================== REFRESH TOKEN ========================
@auth_bp.route("/refresh-token", methods=["POST"])
def refresh_token():
    """
    Renovar token JWT
    ---
    tags:
      - Auth
    summary: Refresh token
    security:
      - BearerAuth: []
    parameters:
      - in: header
        name: Authorization
        type: string
        required: true
        description: "Bearer <token>"
    responses:
      200:
        description: Token renovado
      401:
        description: Token não fornecido / inválido
      404:
        description: Usuário não encontrado
      400:
        description: Erro
    """
    db = SessionLocal()

    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401

        # Remover "Bearer "
        if token.startswith('Bearer '):
            token = token[7:]

        # Decodificar token (mesmo que expirado)
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'], options={"verify_exp": False})

        # Buscar usuário
        usuario = db.query(Usuario).filter(Usuario.id == payload['id']).first()

        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        # Gerar novo token
        new_token = jwt.encode(
            {
                'id': usuario.id,
                'email': usuario.email,
                'tipo': usuario.tipo_usuario,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            SECRET_KEY,
            algorithm='HS256'
        )

        return jsonify({
            'mensagem': 'Token renovado com sucesso',
            'token': new_token
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== LOGOUT ========================
@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Logout
    ---
    tags:
      - Auth
    summary: Logout
    responses:
      200:
        description: Logout realizado com sucesso
    """
    return jsonify({'mensagem': 'Logout realizado com sucesso'}), 200


# ======================== MUDAR SENHA ========================
@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    """
    Alterar senha do usuário
    ---
    tags:
      - Auth
    summary: Alterar senha
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: header
        name: Authorization
        type: string
        required: true
        description: "Bearer <token>"
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [senha_atual, nova_senha]
          properties:
            senha_atual:
              type: string
              example: "123"
            nova_senha:
              type: string
              example: "1234"
    responses:
      200:
        description: Senha alterada com sucesso
      400:
        description: Token e senhas são obrigatórios / erro
      401:
        description: Token inválido/expirado ou senha atual inválida
      404:
        description: Usuário não encontrado
    """
    db = SessionLocal()

    try:
        token = request.headers.get('Authorization')
        data = request.get_json()

        if not token or not data.get('senha_atual') or not data.get('nova_senha'):
            return jsonify({'erro': 'Token e senhas são obrigatórios'}), 400

        # Remover "Bearer "
        if token.startswith('Bearer '):
            token = token[7:]

        # Validar token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        # Buscar usuário
        usuario = db.query(Usuario).filter(Usuario.id == payload['id']).first()

        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        # Verificar senha atual
        if not check_password_hash(usuario.senha, data['senha_atual']):
            return jsonify({'erro': 'Senha atual inválida'}), 401

        # Atualizar para nova senha
        usuario.senha = generate_password_hash(data['nova_senha'])
        db.commit()

        return jsonify({'mensagem': 'Senha alterada com sucesso'}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'erro': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'erro': 'Token inválido'}), 401
    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


# ======================== MIDDLEWARE: DECORATOR PARA PROTEGER ROTAS ========================
from functools import wraps

def token_required(f):
    """Decorator para proteger rotas que requerem autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401

        try:
            if token.startswith('Bearer '):
                token = token[7:]

            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.usuario_id = payload['id']
            request.usuario_tipo = payload['tipo']

        except jwt.ExpiredSignatureError:
            return jsonify({'erro': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'erro': 'Token inválido'}), 401

        return f(*args, **kwargs)

    return decorated

# ======================== REGISTER ORGANIZACAO ========================
@auth_bp.route("/register-organizacao", methods=["POST"])
def register_organizacao():
    """
    Registrar organização + usuário ORGANIZACAO
    ---
    tags:
      - Auth
    summary: Registrar organização
    description: Cria uma organização e um usuário do tipo ORGANIZACAO (sem vínculo no banco).
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [usuario, organizacao]
          properties:
            usuario:
              type: object
              required: [nome, cpf, email, senha]
              properties:
                nome:
                  type: string
                  example: "Admin Org"
                cpf:
                  type: string
                  example: "00000000001"
                email:
                  type: string
                  example: "org1@email.com"
                senha:
                  type: string
                  example: "123"
            organizacao:
              type: object
              required: [nome, cnpj, acesso_ethereum]
              properties:
                nome:
                  type: string
                  example: "Org Teste"
                cnpj:
                  type: string
                  example: "12.345.678/0001-90"
                acesso_ethereum:
                  type: string
                  example: "0xorg"
    responses:
      201:
        description: Organização registrada
      400:
        description: Campos obrigatórios faltando / erro
      409:
        description: Email/CPF/CNPJ já registrado
    """
    db = SessionLocal()

    try:
        data = request.get_json() or {}

        # formato sugerido: { usuario: {...}, organizacao: {...} }
        usuario_data = data.get("usuario") or {}
        org_data = data.get("organizacao") or {}

        required_usuario = ["nome", "cpf", "email", "senha"]
        required_org = ["nome", "cnpj", "acesso_ethereum"]

        if not all(k in usuario_data for k in required_usuario) or not all(k in org_data for k in required_org):
            return jsonify({"erro": "Campos obrigatórios faltando"}), 400

        # valida duplicidade email/cpf
        if db.query(Usuario).filter(Usuario.email == usuario_data["email"]).first():
            return jsonify({"erro": "Email já registrado"}), 409

        if db.query(Usuario).filter(Usuario.cpf == usuario_data["cpf"]).first():
            return jsonify({"erro": "CPF já registrado"}), 409

        # valida duplicidade CNPJ
        if db.query(Organizacao).filter(Organizacao.cnpj == org_data["cnpj"]).first():
            return jsonify({"erro": "CNPJ já registrado"}), 409

        # cria organizacao
        org = Organizacao(
            id=None,
            nome=org_data["nome"],
            cnpj=org_data["cnpj"],
            acesso_ethereum=org_data["acesso_ethereum"],
        )
        db.add(org)
        db.commit()
        db.refresh(org)

        # cria usuario organizacao (sem vínculo no banco, pois falta model/coluna para isso hoje)
        usuario = Usuario(
            nome=usuario_data["nome"],
            cpf=usuario_data["cpf"],
            email=usuario_data["email"],
            senha=generate_password_hash(usuario_data["senha"]),
            tipo_usuario=TipoUsuario.ORGANIZACAO
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        return jsonify({
            "mensagem": "Organização registrada com sucesso",
            "organizacao": {"id": org.id, "nome": org.nome, "cnpj": org.cnpj},
            "usuario": {"id": usuario.id, "email": usuario.email, "tipo": usuario.tipo_usuario},
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()