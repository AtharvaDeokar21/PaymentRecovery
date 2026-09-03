"""Policy evaluation engine for recovery actions."""

from typing import Dict, Any, List
from app.utils.logging import get_logger

logger = get_logger('policy_engine')


class PolicyRuleResult:
    """Result of a single policy rule evaluation."""

    def __init__(self, rule_name: str, passed: bool, reason: str):
        self.rule_name = rule_name
        self.passed = passed
        self.reason = reason


class PolicyEvaluationResult:
    """Result of complete policy evaluation."""

    def __init__(self, allowed: bool, requires_approval: bool, reason: str, rule_results: List[Dict]):
        self.allowed = allowed
        self.requires_approval = requires_approval
        self.reason = reason
        self.rule_results = rule_results


class PolicyEngine:
    """Evaluates whether recovery actions are permitted by policy."""

    @staticmethod
    def evaluate_action(action_type: str, context: Dict[str, Any]) -> PolicyEvaluationResult:
        """
        Evaluate whether an action is allowed by policy.

        Args:
            action_type: Type of action (RETRY, NOTIFY_CUSTOMER, etc.)
            context: Context dict with amount, attempt_number, recovery_probability, etc.

        Returns:
            PolicyEvaluationResult with allowed, requires_approval, reason, and rule details.
        """
        rule_results = []
        all_passed = True
        requires_approval = False

        # Rule 1: Recovery probability threshold
        prob_threshold = context.get('min_recovery_probability', 0.65)
        recovery_prob = context.get('recovery_probability', 0)

        if action_type == 'RETRY':
            if recovery_prob < prob_threshold:
                rule_results.append({
                    'rule': 'recovery_probability_threshold',
                    'passed': False,
                    'reason': f'Recovery probability {recovery_prob:.1%} below threshold {prob_threshold:.1%}'
                })
                all_passed = False
            else:
                rule_results.append({
                    'rule': 'recovery_probability_threshold',
                    'passed': True,
                    'reason': f'Recovery probability {recovery_prob:.1%} meets threshold'
                })

        # Rule 2: Retry attempt limit
        max_attempts = context.get('max_retry_attempts', 2)
        attempt_number = context.get('attempt_number', 1)

        if action_type == 'RETRY':
            if attempt_number >= max_attempts:
                rule_results.append({
                    'rule': 'retry_attempt_limit',
                    'passed': False,
                    'reason': f'Already attempted {attempt_number} times (limit: {max_attempts})'
                })
                all_passed = False
            else:
                rule_results.append({
                    'rule': 'retry_attempt_limit',
                    'passed': True,
                    'reason': f'Attempt {attempt_number} of {max_attempts}'
                })

        # Rule 3: Auto-retry amount limit
        max_auto_amount = context.get('max_auto_retry_amount', 1000000)  # paise
        amount = context.get('amount', 0)

        if action_type == 'RETRY':
            if amount > max_auto_amount:
                requires_approval = True
                rule_results.append({
                    'rule': 'auto_retry_amount_limit',
                    'passed': False,
                    'reason': f'Amount {amount} paise exceeds auto-retry limit {max_auto_amount} paise — requires approval',
                    'requires_approval': True
                })
            else:
                rule_results.append({
                    'rule': 'auto_retry_amount_limit',
                    'passed': True,
                    'reason': f'Amount {amount} paise within auto-retry limit'
                })

        # Rule 4: Failure category restrictions
        failure_category = context.get('failure_category', 'UNKNOWN')

        if action_type == 'RETRY':
            # Don't auto-retry REPEATED_FAILURE or ISSUER_DECLINE
            blocked_categories = ['REPEATED_FAILURE', 'ISSUER_DECLINE']
            if failure_category in blocked_categories:
                rule_results.append({
                    'rule': 'failure_category_restriction',
                    'passed': False,
                    'reason': f'Category {failure_category} should not be auto-retried — requires escalation'
                })
                all_passed = False
            else:
                rule_results.append({
                    'rule': 'failure_category_restriction',
                    'passed': True,
                    'reason': f'Category {failure_category} eligible for retry'
                })

        # Rule 5: Confidence threshold
        min_confidence = context.get('min_confidence_threshold', 0.60)
        confidence = context.get('confidence', 0)

        if confidence < min_confidence:
            rule_results.append({
                'rule': 'confidence_threshold',
                'passed': False,
                'reason': f'Confidence {confidence:.1%} below minimum {min_confidence:.1%}'
            })
            all_passed = False
        else:
            rule_results.append({
                'rule': 'confidence_threshold',
                'passed': True,
                'reason': f'Confidence {confidence:.1%} meets minimum threshold'
            })

        # Rule 6: Cooldown period (not applicable for first retry)
        last_action_at = context.get('last_action_at')
        cooldown_minutes = context.get('cooldown_minutes', 15)

        if action_type == 'RETRY' and last_action_at:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            time_since_last = (now - last_action_at).total_seconds() / 60
            if time_since_last < cooldown_minutes:
                rule_results.append({
                    'rule': 'cooldown_period',
                    'passed': False,
                    'reason': f'Cooldown period active ({cooldown_minutes} min, {time_since_last:.0f} min elapsed)'
                })
                all_passed = False
            else:
                rule_results.append({
                    'rule': 'cooldown_period',
                    'passed': True,
                    'reason': f'Cooldown period satisfied'
                })

        # Determine overall result
        reason = 'Action permitted by policy' if all_passed else 'Action blocked by policy'
        if requires_approval:
            reason = 'Action requires merchant approval'

        allowed = all_passed or requires_approval

        return PolicyEvaluationResult(
            allowed=allowed,
            requires_approval=requires_approval,
            reason=reason,
            rule_results=rule_results
        )


# Singleton instance
_engine = None


def get_policy_engine() -> PolicyEngine:
    """Get the policy engine instance."""
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine
