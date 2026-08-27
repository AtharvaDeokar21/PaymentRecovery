from flask import Blueprint, jsonify, request
from app.services.policy_service import PolicyService

policies_bp = Blueprint('policies', __name__)


@policies_bp.route('/', methods=['GET'])
def get_policies():
    policies = PolicyService.get_policies(merchant_id=1)
    return jsonify(policies)


@policies_bp.route('/', methods=['PUT'])
def update_policies():
    data = request.get_json()
    result = PolicyService.update_policies(merchant_id=1, data=data)
    return jsonify(result)
