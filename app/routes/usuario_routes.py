from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.usuario_cliente import UsuarioCliente
from app.models.endereco import Endereco

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')

# CREATE
@usuarios_bp.route('/cliente', methods=['POST'])
def cadastrar_cliente():
    """
    Cadastrar cliente (sem hash de senha)
    ---
    tags:
      - Usuários
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nome
            - cpf
            - email
            - senha
            - telefone
            - acesso_ethereum
            - endereco
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
                  example: "SP"
                estado:
                  type: string
                  example: "SP"
                cep:
                  type: string
                  example: "01001000"
    responses:
      201:
        description: Cliente criado
      400:
        description: Erro (campos faltando ou falha ao salvar)
    """
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

# READ (ALL)
@usuarios_bp.route('/clientes', methods=['GET'])
def listar_clientes():
    """
    Listar todos os clientes
    ---
    tags:
      - Usuários
    responses:
      200:
        description: Lista de clientes
      404:
        description: Nenhum cliente encontrado
      400:
        description: Erro
    """
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


# READ (ID)
@usuarios_bp.route('/cliente/<int:cliente_id>', methods=['GET'])
def obter_cliente(cliente_id):
    """
    Obter cliente específico por ID
    ---
    tags:
      - Usuários
    parameters:
      - in: path
        name: cliente_id
        type: integer
        required: true
        description: ID do cliente
    responses:
      200:
        description: Cliente encontrado
      404:
        description: Cliente não encontrado
      400:
        description: Erro
    """
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

# UPDATE
@usuarios_bp.route('/cliente/<int:cliente_id>', methods=['PUT'])
def atualizar_cliente(cliente_id):
    """
    Atualizar cliente
    ---
    tags:
      - Usuários
    consumes:
      - application/json
    parameters:
      - in: path
        name: cliente_id
        type: integer
        required: true
        description: ID do cliente
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nome:
              type: string
            email:
              type: string
            senha:
              type: string
            telefone:
              type: string
            acesso_ethereum:
              type: string
            endereco:
              type: object
              properties:
                rua:
                  type: string
                numero:
                  type: integer
                cidade:
                  type: string
                estado:
                  type: string
                cep:
                  type: string
    responses:
      200:
        description: Cliente atualizado
      404:
        description: Cliente não encontrado
      400:
        description: Erro
    """
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


# DELETE
@usuarios_bp.route('/cliente/<int:cliente_id>', methods=['DELETE'])
def deletar_cliente(cliente_id):
    """
    Deletar cliente
    ---
    tags:
      - Usuários
    parameters:
      - in: path
        name: cliente_id
        type: integer
        required: true
        description: ID do cliente
    responses:
      200:
        description: Cliente deletado
      404:
        description: Cliente não encontrado
      400:
        description: Erro
    """
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