"""Simulation adapter for deterministic demo scenarios."""

import random
from typing import Dict, Any
from app.utils.logging import get_logger

logger = get_logger('simulation_adapter')

# Seed for reproducible simulation
_sim_random = random.Random(42)
_sim_counter = 0


class SimulationAdapter:
    """
    Simulated payment gateway for deterministic demonstrations.

    This adapter provides predictable outcomes for demo scenarios.
    No real API calls are made.
    """

    def __init__(self):
        self.mode = 'simulation'
        self._counter = 0

    def _next_id(self, prefix='sim'):
        self._counter += 1
        return f'{prefix}_{self._counter:06d}'

    def create_order(self, amount: int, currency: str = 'INR',
                     receipt: str = None, notes: Dict = None) -> Dict[str, Any]:
        """Create a simulated order."""
        order_id = self._next_id('order_sim')
        logger.info(f"[SIMULATION] Created order {order_id} for ₹{amount/100:.2f}")

        return {
            'success': True,
            'order_id': order_id,
            'amount': amount,
            'currency': currency,
            'status': 'created',
            'mode': self.mode,
            'simulated': True,
        }

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch simulated payment details."""
        logger.info(f"[SIMULATION] Fetching payment {payment_id}")

        return {
            'success': True,
            'payment_id': payment_id,
            'status': 'failed',
            'mode': self.mode,
            'simulated': True,
        }

    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch simulated order details."""
        logger.info(f"[SIMULATION] Fetching order {order_id}")

        return {
            'success': True,
            'order_id': order_id,
            'status': 'created',
            'mode': self.mode,
            'simulated': True,
        }

    def attempt_recovery(self, payment_id: str, amount: int,
                         currency: str = 'INR',
                         force_success: bool = None,
                         recovery_probability: float = None) -> Dict[str, Any]:
        """
        Simulate a recovery attempt with deterministic outcomes.

        Args:
            payment_id: The payment to recover.
            amount: Amount in paise.
            force_success: If set, force this outcome. Used by demo scenarios.
            recovery_probability: If set, use this as success probability.
        """
        # Determine outcome
        if force_success is not None:
            recovered = force_success
        elif recovery_probability is not None:
            recovered = _sim_random.random() < recovery_probability
        else:
            recovered = _sim_random.random() < 0.5

        new_order_id = self._next_id('order_sim')
        new_payment_id = self._next_id('pay_sim')

        if recovered:
            logger.info(f"[SIMULATION] Recovery SUCCESS for {payment_id} — ₹{amount/100:.2f}")
            return {
                'success': True,
                'recovered': True,
                'new_order_id': new_order_id,
                'new_payment_id': new_payment_id,
                'amount': amount,
                'status': 'captured',
                'mode': self.mode,
                'simulated': True,
            }
        else:
            logger.info(f"[SIMULATION] Recovery FAILED for {payment_id}")
            return {
                'success': True,
                'recovered': False,
                'new_order_id': new_order_id,
                'amount': amount,
                'status': 'failed',
                'error': 'Simulated payment failure',
                'mode': self.mode,
                'simulated': True,
            }
