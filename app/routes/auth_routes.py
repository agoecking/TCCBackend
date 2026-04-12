from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import SessionLocal
from app.models.usuario import Usuario, TipoUsuario
from app.models.usuario_cliente import UsuarioCliente
from app.models.endereco import Endereco
import jwt
from datetime import datetime, timedelta
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Chave secreta para JWT (deve estar no .env)
SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-super-segura')


# ======================== REGISTER CLIENTE ========================
@auth_bp.route("/register-cliente", methods=["POST"])
def register_cliente():
    """POST /auth/register-cliente - Registrar novo cliente"""
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
    """POST /auth/login - Login de usuário"""
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


# ======================== VALIDATE TOKEN ========================
@auth_bp.route("/validate-token", methods=["POST"])
def validate_token():
    """POST /auth/validate-token - Validar token JWT"""
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
    """POST /auth/refresh-token - Renovar token JWT"""
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
    """POST /auth/logout - Logout de usuário"""
    return jsonify({'mensagem': 'Logout realizado com sucesso'}), 200


# ======================== CHANGE PASSWORD ========================
@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    """POST /auth/change-password - Alterar senha do usuário"""
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