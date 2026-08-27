from app import db
from app.utils.helpers import utcnow


class RecoveryAction(db.Model):
    __tablename__ = 'recovery_actions'

    id = db.Column(db.Integer, primary_key=True)
    recovery_case_id = db.Column(db.Integer, db.ForeignKey('recovery_cases.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(30), default='RECOMMENDED')
    reason = db.Column(db.Text)
    policy_result = db.Column(db.JSON)
    executed_at = db.Column(db.DateTime(timezone=True))
    result = db.Column(db.JSON)
    recovered_amount = db.Column(db.BigInteger, default=0)  # in paise

    def to_dict(self):
        return {
            'id': self.id,
            'recovery_case_id': self.recovery_case_id,
            'action_type': self.action_type,
            'status': self.status,
            'reason': self.reason,
            'policy_result': self.policy_result,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'result': self.result,
            'recovered_amount': self.recovered_amount,
        }
