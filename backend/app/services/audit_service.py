from app import db
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def list_logs(entity_type=None, page=1, per_page=50):
        query = AuditLog.query
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        query = query.order_by(AuditLog.timestamp.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            'logs': [l.to_dict() for l in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
        }

    @staticmethod
    def get_entity_logs(entity_type, entity_id):
        logs = AuditLog.query.filter_by(
            entity_type=entity_type, entity_id=entity_id
        ).order_by(AuditLog.timestamp.asc()).all()
        return {'logs': [l.to_dict() for l in logs]}

    @staticmethod
    def log(entity_type, entity_id, event_type, actor, action=None,
            input_summary=None, output_summary=None, policy_result=None):
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor=actor,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            policy_result=policy_result,
        )
        db.session.add(entry)
        db.session.commit()
        return entry
