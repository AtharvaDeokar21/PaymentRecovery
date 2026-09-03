"""Payment adapter for simulating recovery attempts."""

from app.utils.logging import get_logger
import random

logger = get_logger('payment_adapter')


class PaymentAdapter:
    """Simulates payment recovery attempts."""

    def attempt_recovery(self, payment_id: str, amount: int, recovery_probability: float = 0.5) -> dict:
        """
        Simulate attempting to recover a failed payment.

        Args:
            payment_id: Payment identifier
            amount: Amount in paise
            recovery_probability: AI-predicted probability of recovery

        Returns:
            Dict with success flag and recovery result.
        """
        logger.info(f"Attempting recovery for {payment_id}, amount={amount}, probability={recovery_probability:.1%}")

        # Simulate recovery based on predicted probability
        # In a real system, this would call the actual payment gateway
        random_roll = random.random()
        success = random_roll < recovery_probability

        if success:
            logger.info(f"Recovery successful for {payment_id}")
            return {
                'success': True,
                'recovered': True,
                'payment_id': payment_id,
                'amount': amount,
                'reason': 'Payment recovered successfully via retry',
            }
        else:
            logger.info(f"Recovery failed for {payment_id}")
            return {
                'success': False,
                'recovered': False,
                'payment_id': payment_id,
                'reason': 'Recovery attempt failed (simulated)',
            }


# Singleton instance
_adapter = None


def get_payment_adapter() -> PaymentAdapter:
    """Get the payment adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = PaymentAdapter()
    return _adapter
