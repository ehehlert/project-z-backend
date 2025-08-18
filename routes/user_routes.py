from flask import Blueprint, request, jsonify
from models.User import User
from models.SLD import SLD
from models.db import db

user_bp = Blueprint('user', __name__, url_prefix='/users')

@user_bp.route('/', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@user_bp.route('/<uuid:user_id>/slds', methods=['GET'])
def get_slds_by_user_company(user_id):
    user = User.query.get_or_404(user_id)

    slds = (
        db.session.query(SLD.id, SLD.name, SLD.is_deleted)
        .filter(SLD.company_id == user.company_id)
        .all()
    )

    result = [
        {
            "id": str(sld.id),
            "name": sld.name,
            "is_deleted": sld.is_deleted
        }
        for sld in slds
    ]

    return jsonify(result), 200