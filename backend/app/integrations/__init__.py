"""Payment gateway integrations."""

from flask import current_app
from app.integrations.razorpay_adapter import RazorpayAdapter
from app.integrations.simulation_adapter import SimulationAdapter


def get_payment_adapter():
    """Get the appropriate payment adapter based on configuration."""
    mode = current_app.config.get('RAZORPAY_MODE', 'simulation')

    if mode == 'test':
        key_id = current_app.config.get('RAZORPAY_KEY_ID', '')
        if key_id and not key_id.startswith('rzp_test_'):
            raise ValueError("RAZORPAY_KEY_ID must be a test-mode key (rzp_test_*). "
                           "Live credentials are not permitted.")
        return RazorpayAdapter()
    else:
        return SimulationAdapter()
