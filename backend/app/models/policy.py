from app import db
from app.utils.helpers import utcnow


class Policy(db.Model):
    __tablename__ = 'policies'

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    max_retry_attempts = db.Column(db.Integer, default=2)
    max_auto_retry_amount = db.Column(db.BigInteger, default=1000000)  # paise = ₹10,000
    min_recovery_probability = db.Column(db.Float, default=0.65)
    approval_threshold = db.Column(db.BigInteger, default=1000000)  # paise = ₹10,000
    cooldown_minutes = db.Column(db.Integer, default=15)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'max_retry_attempts': self.max_retry_attempts,
            'max_auto_retry_amount': self.max_auto_retry_amount,
            'min_recovery_probability': self.min_recovery_probability,
            'approval_threshold': self.approval_threshold,
            'cooldown_minutes': self.cooldown_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
