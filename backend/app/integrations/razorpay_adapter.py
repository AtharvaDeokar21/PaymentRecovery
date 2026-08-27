"""Razorpay test-mode adapter implementing the PaymentGatewayAdapter interface."""

from typing import Dict, Any, Optional
from app.integrations.razorpay_client import RazorpayClient
from app.utils.logging import get_logger

logger = get_logger('razorpay_adapter')


class RazorpayAdapter:
    """
    Payment gateway adapter using real Razorpay test-mode APIs.

    All operations use TEST MODE credentials only.
    Never use live credentials.
    """

    def __init__(self):
        self.client = None
        self.mode = 'test'

    def _get_client(self):
        if self.client is None:
            self.client = RazorpayClient()
        return self.client

    def create_order(self, amount: int, currency: str = 'INR',
                     receipt: str = None, notes: Dict = None) -> Dict[str, Any]:
        """Create a new payment order."""
        try:
            client = self._get_client()
            order = client.create_order(amount, currency, receipt, notes)
            return {
                'success': True,
                'order_id': order.get('id'),
                'amount': order.get('amount'),
                'currency': order.get('currency'),
                'status': order.get('status'),
                'mode': self.mode,
            }
        except Exception as e:
            logger.error(f"Create order failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'mode': self.mode,
            }

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment details from Razorpay."""
        try:
            client = self._get_client()
            payment = client.fetch_payment(payment_id)
            return {
                'success': True,
                'payment_id': payment.get('id'),
                'amount': payment.get('amount'),
                'currency': payment.get('currency'),
                'status': payment.get('status'),
                'method': payment.get('method'),
                'error_code': payment.get('error_code'),
                'error_description': payment.get('error_description'),
                'mode': self.mode,
            }
        except Exception as e:
            logger.error(f"Fetch payment failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'mode': self.mode,
            }

    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch order details from Razorpay."""
        try:
            client = self._get_client()
            order = client.fetch_order(order_id)
            return {
                'success': True,
                'order_id': order.get('id'),
                'amount': order.get('amount'),
                'status': order.get('status'),
                'mode': self.mode,
            }
        except Exception as e:
            logger.error(f"Fetch order failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'mode': self.mode,
            }

    def attempt_recovery(self, payment_id: str, amount: int,
                         currency: str = 'INR') -> Dict[str, Any]:
        """
        Attempt to recover a failed payment by creating a new order.

        In test mode, this creates a new Razorpay order for the same amount.
        The actual payment completion is simulated since test-mode cannot
        programmatically complete payments.
        """
        try:
            client = self._get_client()
            order = client.create_order(
                amount=amount,
                currency=currency,
                receipt=f'recovery_{payment_id}',
                notes={'recovery_for': payment_id}
            )

            return {
                'success': True,
                'recovered': True,
                'new_order_id': order.get('id'),
                'amount': order.get('amount'),
                'status': 'captured',  # Simulated success in test mode
                'mode': self.mode,
                'note': 'Recovery order created in test mode. Payment completion simulated.',
            }
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return {
                'success': False,
                'recovered': False,
                'error': str(e),
                'mode': self.mode,
            }
