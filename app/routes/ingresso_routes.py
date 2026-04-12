from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models.ingresso import Ingresso

ingressos_bp = Blueprint('ingresso', __name__, url_prefix='/ingresso')

