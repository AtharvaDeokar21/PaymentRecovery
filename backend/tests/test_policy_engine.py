"""Test policy engine rules and evaluation."""

import pytest
from datetime import datetime, timedelta, timezone
from app.policies.engine import PolicyEngine, get_policy_engine
from app.policies.defaults import DEFAULT_POLICY


@pytest.fixture
def policy_engine():
    return PolicyEngine()


@pytest.fixture
def base_context():
    """Base context for policy evaluation."""
    return {
        'amount': 500000,  # ₹5,000
        'attempt_number': 1,
        'failure_category': 'TRANSIENT',
        'recovery_probability': 0.75,
        'confidence': 0.80,
        'last_action_at': None,
        'max_retry_attempts': 2,
        'max_auto_retry_amount': 1000000,
        'min_recovery_probability': 0.65,
        'approval_threshold': 1000000,
        'cooldown_minutes': 15,
        'min_confidence_threshold': 0.60,
        'customer_email': 'test@example.com',
        'customer_total_transactions': 10,
        'customer_failed_transactions': 1,
    }


def test_retry_allowed(policy_engine, base_context):
    """Test retry is allowed within limits."""
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is True


def test_retry_blocked_max_attempts(policy_engine, base_context):
    """Test retry is blocked when max attempts exceeded."""
    base_context['attempt_number'] = 3
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is False
    assert 'Maximum retry attempts' in result.reason


def test_retry_blocked_amount_limit(policy_engine, base_context):
    """Test retry is blocked when amount exceeds limit."""
    base_context['amount'] = 2000000  # ₹20,000
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is False or result.requires_approval is True


def test_retry_blocked_low_probability(policy_engine, base_context):
    """Test retry is blocked when probability too low."""
    base_context['recovery_probability'] = 0.50
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is False


def test_retry_blocked_low_confidence(policy_engine, base_context):
    """Test retry is blocked when confidence too low."""
    base_context['confidence'] = 0.50
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is False


def test_retry_blocked_unknown_failure(policy_engine, base_context):
    """Test retry is blocked for unknown failures."""
    base_context['failure_category'] = 'UNKNOWN'
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is False


def test_retry_blocked_repeated_failure(policy_engine, base_context):
    """Test retry is blocked for repeated failures."""
    base_context['failure_category'] = 'REPEATED_FAILURE'
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is False


def test_approval_threshold(policy_engine, base_context):
    """Test high-value payment requires approval."""
    base_context['amount'] = 1500000  # ₹15,000
    result = policy_engine.evaluate_retry(base_context)
    assert result.requires_approval is True


def test_cooldown_enforced(policy_engine, base_context):
    """Test cooldown period is enforced."""
    base_context['last_action_at'] = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is False
    assert 'Cooldown' in result.reason


def test_escalation_always_allowed(policy_engine, base_context):
    """Test escalation is always allowed."""
    result = policy_engine.evaluate_action('ESCALATE', base_context)
    assert result.allowed is True


def test_stop_always_allowed(policy_engine, base_context):
    """Test stop is always allowed."""
    result = policy_engine.evaluate_action('STOP', base_context)
    assert result.allowed is True


def test_notification_allowed(policy_engine, base_context):
    """Test notification is allowed with email."""
    result = policy_engine.evaluate_action('NOTIFY_CUSTOMER', base_context)
    assert result.allowed is True


def test_notification_blocked_no_email(policy_engine, base_context):
    """Test notification is blocked without email."""
    base_context['customer_email'] = None
    result = policy_engine.evaluate_action('NOTIFY_CUSTOMER', base_context)
    assert result.allowed is False


def test_customer_high_failure_rate_blocked(policy_engine, base_context):
    """Test customer with high failure rate is blocked."""
    base_context['customer_failed_transactions'] = 7
    base_context['customer_total_transactions'] = 10
    result = policy_engine.evaluate_retry(base_context)
    assert result.allowed is False
