"""Low-level Razorpay API client."""

import razorpay
from flask import current_app
from app.utils.logging import get_logger

logger = get_logger('razorpay_client')


class RazorpayClient:
    """Thin wrapper around the Razorpay Python SDK."""

    def __init__(self, key_id=None, key_secret=None):
        self.key_id = key_id or current_app.config.get('RAZORPAY_KEY_ID', '')
        self.key_secret = key_secret or current_app.config.get('RAZORPAY_KEY_SECRET', '')
        self.client = None

        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            logger.info("Razorpay client initialized (test mode)")

    @property
    def is_configured(self):
        return self.client is not None

    def create_order(self, amount, currency='INR', receipt=None, notes=None):
        """Create a Razorpay order."""
        if not self.is_configured:
            raise RuntimeError("Razorpay client not configured")

        data = {
            'amount': amount,
            'currency': currency,
        }
        if receipt:
            data['receipt'] = receipt
        if notes:
            data['notes'] = notes

        order = self.client.order.create(data=data)
        logger.info(f"Created order: {order.get('id')}")
        return order

    def fetch_order(self, order_id):
        """Fetch an order by ID."""
        if not self.is_configured:
            raise RuntimeError("Razorpay client not configured")
        return self.client.order.fetch(order_id)

    def fetch_payment(self, payment_id):
        """Fetch a payment by ID."""
        if not self.is_configured:
            raise RuntimeError("Razorpay client not configured")
        return self.client.payment.fetch(payment_id)

    def fetch_order_payments(self, order_id):
        """Fetch all payments for an order."""
        if not self.is_configured:
            raise RuntimeError("Razorpay client not configured")
        return self.client.order.payments(order_id)

    def capture_payment(self, payment_id, amount, currency='INR'):
        """Capture an authorized payment."""
        if not self.is_configured:
            raise RuntimeError("Razorpay client not configured")
        return self.client.payment.capture(payment_id, amount, {"currency": currency})
