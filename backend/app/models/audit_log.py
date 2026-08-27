from app import db
from app.utils.helpers import utcnow


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    actor = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(255))
    input_summary = db.Column(db.JSON)
    output_summary = db.Column(db.JSON)
    policy_result = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'event_type': self.event_type,
            'actor': self.actor,
            'action': self.action,
            'input_summary': self.input_summary,
            'output_summary': self.output_summary,
            'policy_result': self.policy_result,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
