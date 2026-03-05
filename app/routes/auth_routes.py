# from flask import Blueprint, request, jsonify
# from app import db
# from app.models.usuario import Usuario
#
# auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
#
#
# @auth_bp.route("/register", methods=["POST"])
# def register():
#
#     data = request.get_json()
#
#     user = Usuario(
#         nome=data["nome"],
#         email=data["email"],
#         senha=data["senha"],
#         tipo_usuario=data["tipo_usuario"]
#     )
#
#     db.session.add(user)
#     db.session.commit()
#
#     return jsonify({"message": "usuario criado"})