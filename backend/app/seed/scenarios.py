"""Deterministic demo scenarios for RecoverAI."""

SCENARIOS = [
    {
        'id': 'A',
        'name': 'Successful Recovery - Gateway Timeout',
        'description': 'Gateway timeout with strong customer history → retry → success',
        'payment': {
            'amount': 499900,  # ₹4,999 in paise
            'currency': 'INR',
            'payment_method': 'card',
            'failure_code': 'gateway_timeout',
            'failure_reason': 'Payment gateway timed out during processing',
            'attempt_number': 1,
        },
        'customer': {
            'name': 'Priya Sharma',
            'email': 'priya.sharma@example.com',
            'phone': '+919876543210',
            'total_transactions': 8,
            'successful_transactions': 7,
            'failed_transactions': 1,
            'lifetime_value': 3100000,  # ₹31,000
        },
        'expected_outcome': {
            'recovery_probability_min': 0.75,
            'recommended_action': 'RETRY',
            'final_status': 'RECOVERED',
            'recovered_amount': 499900,
        },
    },
    {
        'id': 'B',
        'name': 'Insufficient Funds - Customer Notification',
        'description': 'Insufficient funds → do not retry → notify customer',
        'payment': {
            'amount': 249900,  # ₹2,499
            'currency': 'INR',
            'payment_method': 'card',
            'failure_code': 'insufficient_funds',
            'failure_reason': 'Customer account has insufficient funds',
            'attempt_number': 1,
        },
        'customer': {
            'name': 'Rahul Verma',
            'email': 'rahul.verma@example.com',
            'phone': '+919876543211',
            'total_transactions': 5,
            'successful_transactions': 4,
            'failed_transactions': 1,
            'lifetime_value': 1500000,  # ₹15,000
        },
        'expected_outcome': {
            'recovery_probability_min': 0.3,
            'recommended_action': 'NOTIFY_CUSTOMER',
            'final_status': 'ACTION_PENDING',
            'recovered_amount': 0,
        },
    },
    {
        'id': 'C',
        'name': 'Retry Limit Exceeded - Block & Escalate',
        'description': '3 previous attempts → policy blocks → escalate',
        'payment': {
            'amount': 699900,  # ₹6,999
            'currency': 'INR',
            'payment_method': 'card',
            'failure_code': 'gateway_timeout',
            'failure_reason': 'Repeated gateway timeout',
            'attempt_number': 3,
        },
        'customer': {
            'name': 'Anita Desai',
            'email': 'anita.desai@example.com',
            'phone': '+919876543212',
            'total_transactions': 12,
            'successful_transactions': 9,
            'failed_transactions': 3,
            'lifetime_value': 4500000,  # ₹45,000
        },
        'expected_outcome': {
            'recovery_probability_min': 0.2,
            'recommended_action': 'ESCALATE',
            'final_status': 'ESCALATED',
            'recovered_amount': 0,
        },
    },
    {
        'id': 'D',
        'name': 'High-Value Payment - Requires Approval',
        'description': '₹25,000 exceeds auto-retry limit → requires merchant approval',
        'payment': {
            'amount': 2500000,  # ₹25,000
            'currency': 'INR',
            'payment_method': 'netbanking',
            'failure_code': 'gateway_timeout',
            'failure_reason': 'Bank gateway timeout during high-value transaction',
            'attempt_number': 1,
        },
        'customer': {
            'name': 'Vikram Singh',
            'email': 'vikram.singh@example.com',
            'phone': '+919876543213',
            'total_transactions': 15,
            'successful_transactions': 14,
            'failed_transactions': 1,
            'lifetime_value': 12000000,  # ₹1,20,000
        },
        'expected_outcome': {
            'recovery_probability_min': 0.7,
            'recommended_action': 'ESCALATE',
            'final_status': 'ESCALATED',
            'recovered_amount': 0,
        },
    },
    {
        'id': 'E',
        'name': 'Unknown Failure - Human Escalation',
        'description': 'Unknown failure code → must escalate to human review',
        'payment': {
            'amount': 899900,  # ₹8,999
            'currency': 'INR',
            'payment_method': 'wallet',
            'failure_code': 'internal_error_xyz',
            'failure_reason': 'An unknown internal error occurred',
            'attempt_number': 1,
        },
        'customer': {
            'name': 'Meera Patel',
            'email': 'meera.patel@example.com',
            'phone': '+919876543214',
            'total_transactions': 3,
            'successful_transactions': 2,
            'failed_transactions': 1,
            'lifetime_value': 700000,  # ₹7,000
        },
        'expected_outcome': {
            'recovery_probability_min': 0.1,
            'recommended_action': 'ESCALATE',
            'final_status': 'ESCALATED',
            'recovered_amount': 0,
        },
    },
]
