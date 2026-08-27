from app import db
from app.models.payment import Payment
from app.models.customer import Customer


class PaymentService:
    @staticmethod
    def list_payments(status=None, page=1, per_page=20):
        query = Payment.query
        if status:
            query = query.filter(Payment.status == status)
        query = query.order_by(Payment.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            'payments': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        }

    @staticmethod
    def get_payment(payment_id):
        payment = Payment.query.get(payment_id)
        if not payment:
            return None
        result = payment.to_dict()
        result['customer'] = payment.customer.to_dict() if payment.customer else None
        return result
