from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.usuario_cliente import UsuarioCliente
from app.models.endereco import Endereco

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')


@usuarios_bp.route('/cliente', methods=['POST'])
def cadastrar_cliente():
    """POST /api/usuarios/cliente"""
    db = SessionLocal()

    try:
        data = request.get_json()

        # Criar endereço
        endereco = Endereco(
            rua=data['endereco']['rua'],
            numero=data['endereco']['numero'],
            cidade=data['endereco']['cidade'],
            estado=data['endereco']['estado'],
            cep=data['endereco']['cep']
        )

        # Criar usuário
        usuario = UsuarioCliente(
            nome=data['nome'],
            cpf=data['cpf'],
            email=data['email'],
            senha=data['senha'],
            telefone=data['telefone'],
            acesso_ethereum=data['acesso_ethereum'],
            endereco=endereco
        )

        # Salvar no banco
        db.add(endereco)
        db.add(usuario)
        db.commit()

        return jsonify({
            'id': usuario.id,
            'nome': usuario.nome,
            'email': usuario.email
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()