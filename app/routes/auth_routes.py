from flask import Blueprint, request, jsonify
from app import db
from app.models.usuario import Usuario

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register-cliente", methods=["POST"])
def register_cliente():
    data = request.get_json()

