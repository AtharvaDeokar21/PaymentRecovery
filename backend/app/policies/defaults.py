"""Default policy configuration values."""

DEFAULT_POLICY = {
    'max_retry_attempts': 2,
    'max_auto_retry_amount': 1000000,      # ₹10,000 in paise
    'min_recovery_probability': 0.65,
    'approval_threshold': 1000000,          # ₹10,000 in paise
    'cooldown_minutes': 15,
    'min_confidence_threshold': 0.60,
    'notification_enabled': True,
    'auto_escalate_unknown': True,
}

# Failure categories that should always escalate
ALWAYS_ESCALATE_CATEGORIES = ['UNKNOWN', 'REPEATED_FAILURE']

# Maximum number of notifications per customer per day
MAX_NOTIFICATIONS_PER_DAY = 2
