from flask import Blueprint, jsonify, request
from app.services.payment_service import PaymentService

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/')
def list_payments():
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result = PaymentService.list_payments(status=status, page=page, per_page=per_page)
    return jsonify(result)


@payments_bp.route('/<int:payment_id>')
def get_payment(payment_id):
    payment = PaymentService.get_payment(payment_id)
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    return jsonify(payment)
