from app import db
from app.utils.helpers import utcnow


class PaymentEvent(db.Model):
    __tablename__ = 'payment_events'

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(db.JSON, default=dict)
    timestamp = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
