from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def format_currency(amount_paise: int, currency: str = 'INR') -> str:
    """Format amount from paise to rupees display."""
    rupees = amount_paise / 100
    if currency == 'INR':
        if rupees >= 100000:
            return f'₹{rupees / 100000:.2f}L'
        elif rupees >= 1000:
            return f'₹{rupees / 1000:.1f}K'
        return f'₹{rupees:,.0f}'
    return f'{rupees:,.2f} {currency}'


def classify_failure(failure_code: str, attempt_number: int = 1) -> str:
    """Classify a failure code into a failure category."""
    transient = {'gateway_timeout', 'network_error', 'temporary_bank_unavailable', 'processing_timeout'}
    customer_funds = {'insufficient_funds', 'limit_exceeded'}
    payment_method = {'expired_card', 'invalid_card', 'unsupported_method'}
    issuer_decline = {'issuer_declined', 'do_not_honor'}

    code = (failure_code or '').lower().strip()

    if attempt_number >= 3:
        return 'REPEATED_FAILURE'
    if code in transient:
        return 'TRANSIENT'
    if code in customer_funds:
        return 'CUSTOMER_FUNDS'
    if code in payment_method:
        return 'PAYMENT_METHOD'
    if code in issuer_decline:
        return 'ISSUER_DECLINE'
    return 'UNKNOWN'
