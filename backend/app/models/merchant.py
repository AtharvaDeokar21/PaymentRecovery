from app import db
from app.utils.helpers import utcnow


class Merchant(db.Model):
    __tablename__ = 'merchants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    currency = db.Column(db.String(10), default='INR')
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    customers = db.relationship('Customer', backref='merchant', lazy='dynamic')
    payments = db.relationship('Payment', backref='merchant', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
