from flask import Blueprint, jsonify, request
from app.services.audit_service import AuditService

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/')
def list_audit_logs():
    entity_type = request.args.get('entity_type')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    result = AuditService.list_logs(entity_type=entity_type, page=page, per_page=per_page)
    return jsonify(result)


@audit_bp.route('/<int:entity_id>')
def get_entity_logs(entity_id):
    entity_type = request.args.get('entity_type', 'recovery_case')
    logs = AuditService.get_entity_logs(entity_type=entity_type, entity_id=entity_id)
    return jsonify(logs)
