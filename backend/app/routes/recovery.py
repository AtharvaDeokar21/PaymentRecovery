from flask import Blueprint, jsonify, request
from app.services.recovery_service import RecoveryService

recovery_bp = Blueprint('recovery', __name__)


@recovery_bp.route('/cases')
def list_cases():
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result = RecoveryService.list_cases(status=status, page=page, per_page=per_page)
    return jsonify(result)


@recovery_bp.route('/cases/<int:case_id>')
def get_case(case_id):
    case = RecoveryService.get_case_detail(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    return jsonify(case)


@recovery_bp.route('/cases/<int:case_id>/analyze', methods=['POST'])
def analyze_case(case_id):
    result = RecoveryService.analyze_case(case_id)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)


@recovery_bp.route('/cases/<int:case_id>/execute', methods=['POST'])
def execute_case(case_id):
    result = RecoveryService.execute_recovery(case_id)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)


@recovery_bp.route('/cases/<int:case_id>/escalate', methods=['POST'])
def escalate_case(case_id):
    result = RecoveryService.escalate_case(case_id)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)
