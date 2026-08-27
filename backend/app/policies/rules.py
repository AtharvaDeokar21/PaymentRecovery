"""Individual policy validation rules."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from app.policies.defaults import ALWAYS_ESCALATE_CATEGORIES, DEFAULT_POLICY


class PolicyRule:
    """Base class for a policy rule."""

    def __init__(self, name: str):
        self.name = name

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class RetryLimitRule(PolicyRule):
    """Check if retry attempt count is within limits."""

    def __init__(self):
        super().__init__('retry_limit')

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        attempt_number = context.get('attempt_number', 1)
        max_retries = context.get('max_retry_attempts', DEFAULT_POLICY['max_retry_attempts'])

        allowed = attempt_number < max_retries
        return {
            'rule': self.name,
            'allowed': allowed,
            'reason': f'Attempt {attempt_number}/{max_retries}' if allowed
                     else f'Maximum retry attempts ({max_retries}) reached',
            'details': {'attempt_number': attempt_number, 'max_retries': max_retries}
        }


class AmountLimitRule(PolicyRule):
    """Check if amount is within auto-retry limits."""

    def __init__(self):
        super().__init__('amount_limit')

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        amount = context.get('amount', 0)
        max_amount = context.get('max_auto_retry_amount', DEFAULT_POLICY['max_auto_retry_amount'])

        allowed = amount <= max_amount
        return {
            'rule': self.name,
            'allowed': allowed,
            'reason': f'Amount ₹{amount/100:.0f} within limit ₹{max_amount/100:.0f}' if allowed
                     else f'Amount ₹{amount/100:.0f} exceeds auto-retry limit ₹{max_amount/100:.0f}',
            'details': {'amount': amount, 'max_amount': max_amount}
        }


class ProbabilityThresholdRule(PolicyRule):
    """Check if recovery probability meets minimum threshold."""

    def __init__(self):
        super().__init__('probability_threshold')

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        probability = context.get('recovery_probability', 0)
        threshold = context.get('min_recovery_probability', DEFAULT_POLICY['min_recovery_probability'])

        allowed = probability >= threshold
        return {
            'rule': self.name,
            'allowed': allowed,
            'reason': f'Recovery probability {probability:.1%} meets threshold {threshold:.1%}' if allowed
                     else f'Recovery probability {probability:.1%} below threshold {threshold:.1%}',
            'details': {'probability': probability, 'threshold': threshold}
        }


class CooldownRule(PolicyRule):
    """Check if cooldown period has elapsed since last action."""

    def __init__(self):
        super().__init__('cooldown')

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        last_action_at = context.get('last_action_at')
        cooldown_minutes = context.get('cooldown_minutes', DEFAULT_POLICY['cooldown_minutes'])

        if last_action_at is None:
            return {
                'rule': self.name,
                'allowed': True,
                'reason': 'No previous action — cooldown not applicable',
                'details': {'cooldown_minutes': cooldown_minutes}
            }

        if isinstance(last_action_at, str):
            last_action_at = datetime.fromisoformat(last_action_at.replace('Z', '+00:00'))

        now = datetime.now(timezone.utc)
        elapsed = (now - last_action_at).total_seconds() / 60
        allowed = elapsed >= cooldown_minutes

        return {
            'rule': self.name,
            'allowed': allowed,
            'reason': f'Cooldown elapsed ({elapsed:.0f}m >= {cooldown_minutes}m)' if allowed
                     else f'Cooldown active ({elapsed:.0f}m < {cooldown_minutes}m)',
            'details': {
                'elapsed_minutes': round(elapsed, 1),
                'cooldown_minutes': cooldown_minutes,
            }
        }


class ApprovalThresholdRule(PolicyRule):
    """Check if amount requires merchant approval."""

    def __init__(self):
        super().__init__('approval_threshold')

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        amount = context.get('amount', 0)
        threshold = context.get('approval_threshold', DEFAULT_POLICY['approval_threshold'])

        requires_approval = amount > threshold
        return {
            'rule': self.name,
            'allowed': not requires_approval,
            'requires_approval': requires_approval,
            'reason': f'Amount ₹{amount/100:.0f} requires merchant approval (threshold ₹{threshold/100:.0f})' if requires_approval
                     else f'Amount ₹{amount/100:.0f} within auto-approval limit',
            'details': {'amount': amount, 'threshold': threshold}
        }


class ConfidenceRule(PolicyRule):
    """Check if agent confidence is above threshold."""

    def __init__(self):
        super().__init__('confidence')

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        confidence = context.get('confidence', 0)
        threshold = context.get('min_confidence_threshold', DEFAULT_POLICY['min_confidence_threshold'])

        allowed = confidence >= threshold
        return {
            'rule': self.name,
            'allowed': allowed,
            'reason': f'Confidence {confidence:.1%} meets threshold {threshold:.1%}' if allowed
                     else f'Low confidence {confidence:.1%} — escalation required',
            'details': {'confidence': confidence, 'threshold': threshold}
        }


class FailureCategoryRule(PolicyRule):
    """Check if failure category allows automated action."""

    def __init__(self):
        super().__init__('failure_category')

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        category = context.get('failure_category', 'UNKNOWN')

        must_escalate = category in ALWAYS_ESCALATE_CATEGORIES
        return {
            'rule': self.name,
            'allowed': not must_escalate,
            'reason': f'{category} failure requires human review' if must_escalate
                     else f'{category} failure eligible for automated recovery',
            'details': {'category': category, 'must_escalate': must_escalate}
        }


class CustomerEligibilityRule(PolicyRule):
    """Check if customer is eligible for recovery actions."""

    def __init__(self):
        super().__init__('customer_eligibility')

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        customer_failed = context.get('customer_failed_transactions', 0)
        customer_total = context.get('customer_total_transactions', 1)

        # Block if customer has excessive failure rate (> 70%)
        failure_rate = customer_failed / max(customer_total, 1)
        allowed = failure_rate < 0.7

        return {
            'rule': self.name,
            'allowed': allowed,
            'reason': f'Customer failure rate {failure_rate:.1%} acceptable' if allowed
                     else f'Customer failure rate {failure_rate:.1%} too high — recovery blocked',
            'details': {
                'failure_rate': round(failure_rate, 4),
                'failed': customer_failed,
                'total': customer_total,
            }
        }
