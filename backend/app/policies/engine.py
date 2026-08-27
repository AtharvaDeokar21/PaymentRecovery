"""Policy engine — validates all recovery actions independently from the LLM."""

from typing import Dict, Any, List
from dataclasses import dataclass, field, asdict
from app.policies.rules import (
    RetryLimitRule,
    AmountLimitRule,
    ProbabilityThresholdRule,
    CooldownRule,
    ApprovalThresholdRule,
    ConfidenceRule,
    FailureCategoryRule,
    CustomerEligibilityRule,
)
from app.policies.defaults import DEFAULT_POLICY
from app.utils.logging import get_logger

logger = get_logger('policy_engine')


@dataclass
class PolicyResult:
    """Result of a policy evaluation."""
    allowed: bool
    requires_approval: bool = False
    reason: str = ''
    rule_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class PolicyEngine:
    """
    Validates recovery actions independently from the LLM.

    The LLM recommends; the policy engine decides.
    The LLM CANNOT bypass this engine.
    """

    def __init__(self):
        self.retry_rules = [
            RetryLimitRule(),
            AmountLimitRule(),
            ProbabilityThresholdRule(),
            CooldownRule(),
            ApprovalThresholdRule(),
            ConfidenceRule(),
            FailureCategoryRule(),
            CustomerEligibilityRule(),
        ]

        self.notification_rules = [
            CustomerEligibilityRule(),
        ]

        self.escalation_rules = []  # Escalation is always allowed

    def evaluate_retry(self, context: Dict[str, Any]) -> PolicyResult:
        """Evaluate whether a retry action is permitted."""
        logger.info(f"Evaluating RETRY policy for payment amount={context.get('amount')}")

        results = []
        all_allowed = True
        requires_approval = False
        reasons = []

        for rule in self.retry_rules:
            result = rule.evaluate(context)
            results.append(result)

            if not result['allowed']:
                all_allowed = False
                reasons.append(result['reason'])

            if result.get('requires_approval'):
                requires_approval = True
                reasons.append(result['reason'])

        if requires_approval:
            return PolicyResult(
                allowed=False,
                requires_approval=True,
                reason='Requires merchant approval: ' + '; '.join(reasons),
                rule_results=results,
            )

        return PolicyResult(
            allowed=all_allowed,
            requires_approval=False,
            reason='All policy checks passed' if all_allowed else 'Blocked: ' + '; '.join(reasons),
            rule_results=results,
        )

    def evaluate_notification(self, context: Dict[str, Any]) -> PolicyResult:
        """Evaluate whether a notification action is permitted."""
        logger.info(f"Evaluating NOTIFICATION policy")

        results = []
        all_allowed = True
        reasons = []

        for rule in self.notification_rules:
            result = rule.evaluate(context)
            results.append(result)
            if not result['allowed']:
                all_allowed = False
                reasons.append(result['reason'])

        # Check contact info
        has_email = bool(context.get('customer_email'))
        if not has_email:
            all_allowed = False
            reasons.append('No customer email available')
            results.append({'rule': 'contact_info', 'allowed': False, 'reason': 'No email'})

        return PolicyResult(
            allowed=all_allowed,
            reason='Notification permitted' if all_allowed else 'Blocked: ' + '; '.join(reasons),
            rule_results=results,
        )

    def evaluate_action(self, action_type: str, context: Dict[str, Any]) -> PolicyResult:
        """Evaluate any action type against policy."""
        if action_type == 'RETRY':
            return self.evaluate_retry(context)
        elif action_type == 'NOTIFY_CUSTOMER':
            return self.evaluate_notification(context)
        elif action_type == 'ESCALATE':
            return PolicyResult(
                allowed=True,
                reason='Escalation is always permitted',
                rule_results=[],
            )
        elif action_type == 'STOP':
            return PolicyResult(
                allowed=True,
                reason='Stop is always permitted',
                rule_results=[],
            )
        elif action_type == 'ALTERNATE_PAYMENT':
            return self.evaluate_notification(context)  # Same rules as notification
        else:
            return PolicyResult(
                allowed=False,
                reason=f'Unknown action type: {action_type}',
                rule_results=[],
            )


# Singleton
_engine = None


def get_policy_engine() -> PolicyEngine:
    """Get or create the singleton policy engine."""
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine
