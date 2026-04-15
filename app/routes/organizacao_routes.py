from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.organizacao import Organizacao

organizacoes_bp = Blueprint("organizacoes", __name__, url_prefix="/api/organizacoes")


@organizacoes_bp.route("", methods=["POST"])
def criar_organizacao():
    """POST /api/organizacoes - Criar organização"""
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
    """GET /api/organizacoes - Listar organizações"""
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
    """GET /api/organizacoes/{id} - Obter organização"""
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
    """PUT /api/organizacoes/{id} - Atualizar organização"""
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
    """DELETE /api/organizacoes/{id} - Deletar organização"""
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