from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.usuario_cliente import UsuarioCliente
from app.models.endereco import Endereco

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')

#CREATE
@usuarios_bp.route('/cliente', methods=['POST'])
def cadastrar_cliente():
    db = SessionLocal()

    try:
        data = request.get_json()

        if not all(k in data for k in ['nome', 'cpf', 'email', 'senha', 'telefone', 'acesso_ethereum', 'endereco']):
            return jsonify({'erro': 'Campos obrigatórios faltando'}), 400

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
            'email': usuario.email,
            'cpf': usuario.cpf,
            'telefone': usuario.telefone
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()

#READ (ALL)
@usuarios_bp.route('/clientes', methods=['GET'])
def listar_clientes():
    """GET /api/usuarios/clientes - Listar todos os clientes"""
    db = SessionLocal()

    try:
        clientes = db.query(UsuarioCliente).all()

        if not clientes:
            return jsonify({'mensagem': 'Nenhum cliente encontrado'}), 404

        resultado = []
        for cliente in clientes:
            resultado.append({
                'id': cliente.id,
                'nome': cliente.nome,
                'email': cliente.email,
                'cpf': cliente.cpf,
                'telefone': cliente.telefone,
                'acesso_ethereum': cliente.acesso_ethereum,
                'endereco': {
                    'rua': cliente.endereco.rua if cliente.endereco else None,
                    'numero': cliente.endereco.numero if cliente.endereco else None,
                    'cidade': cliente.endereco.cidade if cliente.endereco else None,
                    'estado': cliente.endereco.estado if cliente.endereco else None,
                    'cep': cliente.endereco.cep if cliente.endereco else None,
                }
            })

        return jsonify({'clientes': resultado, 'total': len(resultado)}), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


#READ (ID)
@usuarios_bp.route('/cliente/<int:cliente_id>', methods=['GET'])
def obter_cliente(cliente_id):
    """GET /api/usuarios/cliente/{id} - Obter cliente específico"""
    db = SessionLocal()

    try:
        cliente = db.query(UsuarioCliente).filter(UsuarioCliente.id == cliente_id).first()

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        return jsonify({
            'id': cliente.id,
            'nome': cliente.nome,
            'email': cliente.email,
            'cpf': cliente.cpf,
            'telefone': cliente.telefone,
            'acesso_ethereum': cliente.acesso_ethereum,
            'endereco': {
                'rua': cliente.endereco.rua if cliente.endereco else None,
                'numero': cliente.endereco.numero if cliente.endereco else None,
                'cidade': cliente.endereco.cidade if cliente.endereco else None,
                'estado': cliente.endereco.estado if cliente.endereco else None,
                'cep': cliente.endereco.cep if cliente.endereco else None,
            }
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()

#UPDATE
@usuarios_bp.route('/cliente/<int:cliente_id>', methods=['PUT'])
def atualizar_cliente(cliente_id):
    """PUT /api/usuarios/cliente/{id} - Atualizar cliente"""
    db = SessionLocal()

    try:
        cliente = db.query(UsuarioCliente).filter(UsuarioCliente.id == cliente_id).first()

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        data = request.get_json()

        # Atualizar campos do usuário
        if 'nome' in data:
            cliente.nome = data['nome']
        if 'email' in data:
            cliente.email = data['email']
        if 'senha' in data:
            cliente.senha = data['senha']
        if 'telefone' in data:
            cliente.telefone = data['telefone']
        if 'acesso_ethereum' in data:
            cliente.acesso_ethereum = data['acesso_ethereum']

        # Atualizar endereço se fornecido
        if 'endereco' in data and cliente.endereco:
            endereco_data = data['endereco']
            if 'rua' in endereco_data:
                cliente.endereco.rua = endereco_data['rua']
            if 'numero' in endereco_data:
                cliente.endereco.numero = endereco_data['numero']
            if 'cidade' in endereco_data:
                cliente.endereco.cidade = endereco_data['cidade']
            if 'estado' in endereco_data:
                cliente.endereco.estado = endereco_data['estado']
            if 'cep' in endereco_data:
                cliente.endereco.cep = endereco_data['cep']

        db.commit()

        return jsonify({
            'mensagem': 'Cliente atualizado com sucesso',
            'id': cliente.id,
            'nome': cliente.nome,
            'email': cliente.email
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()


#DELETE
@usuarios_bp.route('/cliente/<int:cliente_id>', methods=['DELETE'])
def deletar_cliente(cliente_id):
    """DELETE /api/usuarios/cliente/{id} - Deletar cliente"""
    db = SessionLocal()

    try:
        cliente = db.query(UsuarioCliente).filter(UsuarioCliente.id == cliente_id).first()

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Deletar endereço associado também
        if cliente.endereco:
            db.delete(cliente.endereco)

        # Deletar cliente
        db.delete(cliente)
        db.commit()

        return jsonify({'mensagem': 'Cliente deletado com sucesso'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db.close()