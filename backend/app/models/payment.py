from app import db
from app.utils.helpers import utcnow


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    razorpay_order_id = db.Column(db.String(255))
    razorpay_payment_id = db.Column(db.String(255))
    amount = db.Column(db.BigInteger, nullable=False)  # in paise
    currency = db.Column(db.String(10), default='INR')
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='failed')
    failure_code = db.Column(db.String(100))
    failure_reason = db.Column(db.Text)
    attempt_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    events = db.relationship('PaymentEvent', backref='payment', lazy='dynamic')
    recovery_case = db.relationship('RecoveryCase', backref='payment', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'customer_id': self.customer_id,
            'razorpay_order_id': self.razorpay_order_id,
            'razorpay_payment_id': self.razorpay_payment_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'status': self.status,
            'failure_code': self.failure_code,
            'failure_reason': self.failure_reason,
            'attempt_number': self.attempt_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
