from app import db
from app.utils.helpers import utcnow


class AgentDecision(db.Model):
    __tablename__ = 'agent_decisions'

    id = db.Column(db.Integer, primary_key=True)
    recovery_case_id = db.Column(db.Integer, db.ForeignKey('recovery_cases.id'), nullable=False)
    diagnosis = db.Column(db.String(100))
    reasoning_summary = db.Column(db.Text)
    confidence = db.Column(db.Float)
    recommended_action = db.Column(db.String(50))
    tool_calls = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'recovery_case_id': self.recovery_case_id,
            'diagnosis': self.diagnosis,
            'reasoning_summary': self.reasoning_summary,
            'confidence': self.confidence,
            'recommended_action': self.recommended_action,
            'tool_calls': self.tool_calls,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
