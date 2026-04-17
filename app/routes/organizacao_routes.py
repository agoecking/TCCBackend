from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.organizacao import Organizacao

organizacoes_bp = Blueprint("organizacoes", __name__, url_prefix="/api/organizacoes")


@organizacoes_bp.route("", methods=["POST"])
def criar_organizacao():
    """
    Criar organização
    ---
    tags:
      - Organizações
    summary: Criar organização
    description: Cria uma organização (CNPJ deve ser único).
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
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
        description: Organização criada
      400:
        description: Erro (campos faltando ou falha ao salvar)
      409:
        description: CNPJ já registrado
    """
    db = SessionLocal()
    try:
        data = request.get_json() or {}

        required = ["nome", "cnpj", "acesso_ethereum"]
        if not all(k in data for k in required):
            return jsonify({"erro": "Campos obrigatórios faltando"}), 400

        # checar CNPJ duplicado (cnpj é unique no model)
        existente = db.query(Organizacao).filter(Organizacao.cnpj == data["cnpj"]).first()
        if existente:
            return jsonify({"erro": "CNPJ já registrado"}), 409

        org = Organizacao(
            id=None,
            nome=data["nome"],
            cnpj=data["cnpj"],
            acesso_ethereum=data["acesso_ethereum"],
        )

        db.add(org)
        db.commit()
        db.refresh(org)

        return jsonify({
            "mensagem": "Organização criada com sucesso",
            "id": org.id,
            "nome": org.nome,
            "cnpj": org.cnpj,
            "acesso_ethereum": org.acesso_ethereum,
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()


@organizacoes_bp.route("", methods=["GET"])
def listar_organizacoes():
    """
    Listar organizações
    ---
    tags:
      - Organizações
    summary: Listar organizações
    responses:
      200:
        description: Lista de organizações
      400:
        description: Erro
    """
    db = SessionLocal()
    try:
        orgs = db.query(Organizacao).all()
        return jsonify([{
            "id": o.id,
            "nome": o.nome,
            "cnpj": o.cnpj,
            "acesso_ethereum": o.acesso_ethereum,
        } for o in orgs]), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()


@organizacoes_bp.route("/<int:org_id>", methods=["GET"])
def obter_organizacao(org_id):
    """
    Obter organização por ID
    ---
    tags:
      - Organizações
    summary: Obter organização
    parameters:
      - in: path
        name: org_id
        type: integer
        required: true
        description: ID da organização
    responses:
      200:
        description: Organização encontrada
      404:
        description: Organização não encontrada
      400:
        description: Erro
    """
    db = SessionLocal()
    try:
        org = db.query(Organizacao).filter(Organizacao.id == org_id).first()
        if not org:
            return jsonify({"erro": "Organização não encontrada"}), 404

        return jsonify({
            "id": org.id,
            "nome": org.nome,
            "cnpj": org.cnpj,
            "acesso_ethereum": org.acesso_ethereum,
        }), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()


@organizacoes_bp.route("/<int:org_id>", methods=["PUT"])
def atualizar_organizacao(org_id):
    """
    Atualizar organização
    ---
    tags:
      - Organizações
    summary: Atualizar organização
    consumes:
      - application/json
    parameters:
      - in: path
        name: org_id
        type: integer
        required: true
        description: ID da organização
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nome:
              type: string
              example: "Org Atualizada"
            cnpj:
              type: string
              example: "12.345.678/0001-90"
            acesso_ethereum:
              type: string
              example: "0xorg"
    responses:
      200:
        description: Organização atualizada
      404:
        description: Organização não encontrada
      409:
        description: CNPJ já registrado
      400:
        description: Erro
    """
    db = SessionLocal()
    try:
        org = db.query(Organizacao).filter(Organizacao.id == org_id).first()
        if not org:
            return jsonify({"erro": "Organização não encontrada"}), 404

        data = request.get_json() or {}

        if "nome" in data:
            org.nome = data["nome"]

        if "cnpj" in data:
            # checar duplicidade
            existe = db.query(Organizacao).filter(
                Organizacao.cnpj == data["cnpj"],
                Organizacao.id != org_id
            ).first()
            if existe:
                return jsonify({"erro": "CNPJ já registrado"}), 409
            org.cnpj = data["cnpj"]

        if "acesso_ethereum" in data:
            org.acesso_ethereum = data["acesso_ethereum"]

        db.commit()
        db.refresh(org)

        return jsonify({
            "mensagem": "Organização atualizada com sucesso",
            "id": org.id,
            "nome": org.nome,
            "cnpj": org.cnpj,
            "acesso_ethereum": org.acesso_ethereum,
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()


@organizacoes_bp.route("/<int:org_id>", methods=["DELETE"])
def deletar_organizacao(org_id):
    """
    Deletar organização
    ---
    tags:
      - Organizações
    summary: Deletar organização
    description: Remove uma organização. Se houver eventos associados, retorna 409.
    parameters:
      - in: path
        name: org_id
        type: integer
        required: true
        description: ID da organização
    responses:
      200:
        description: Organização deletada
      404:
        description: Organização não encontrada
      409:
        description: Organização possui eventos e não pode ser removida
      400:
        description: Erro
    """
    db = SessionLocal()
    try:
        org = db.query(Organizacao).filter(Organizacao.id == org_id).first()
        if not org:
            return jsonify({"erro": "Organização não encontrada"}), 404

        # regra: se existir evento associado, bloqueia (pra não quebrar FK)
        if org.eventos and len(org.eventos) > 0:
            return jsonify({"erro": "Organização possui eventos e não pode ser removida"}), 409

        db.delete(org)
        db.commit()
        return jsonify({"mensagem": "Organização deletada com sucesso"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()