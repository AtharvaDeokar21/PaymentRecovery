from app import db
from app.utils.helpers import utcnow


class RecoveryCase(db.Model):
    __tablename__ = 'recovery_cases'

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False, unique=True)
    status = db.Column(db.String(30), default='DETECTED')
    recovery_probability = db.Column(db.Float)
    revenue_at_risk = db.Column(db.BigInteger)  # in paise
    expected_recovery = db.Column(db.BigInteger)  # in paise
    diagnosis = db.Column(db.Text)
    recommended_action = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    priority = db.Column(db.String(20), default='MEDIUM')
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    actions = db.relationship('RecoveryAction', backref='recovery_case', lazy='dynamic')
    decisions = db.relationship('AgentDecision', backref='recovery_case', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'status': self.status,
            'recovery_probability': self.recovery_probability,
            'revenue_at_risk': self.revenue_at_risk,
            'expected_recovery': self.expected_recovery,
            'diagnosis': self.diagnosis,
            'recommended_action': self.recommended_action,
            'confidence': self.confidence,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
