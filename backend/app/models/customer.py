from app import db
from app.utils.helpers import utcnow


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    external_customer_id = db.Column(db.String(255))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    total_transactions = db.Column(db.Integer, default=0)
    successful_transactions = db.Column(db.Integer, default=0)
    failed_transactions = db.Column(db.Integer, default=0)
    lifetime_value = db.Column(db.BigInteger, default=0)  # in paise
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    payments = db.relationship('Payment', backref='customer', lazy='dynamic')

    @property
    def success_rate(self):
        if self.total_transactions == 0:
            return 0.0
        return self.successful_transactions / self.total_transactions

    def to_dict(self):
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'external_customer_id': self.external_customer_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'total_transactions': self.total_transactions,
            'successful_transactions': self.successful_transactions,
            'failed_transactions': self.failed_transactions,
            'lifetime_value': self.lifetime_value,
            'success_rate': round(self.success_rate, 4),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
