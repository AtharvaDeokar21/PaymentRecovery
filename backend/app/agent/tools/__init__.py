"""Tool implementations for the recovery agent."""

from app import db
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.agent_decision import AgentDecision
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.logging import get_logger
from app.policies.engine import get_policy_engine
from app.ml.predictor import get_predictor
from app.utils.helpers import classify_failure
from app.integrations import get_payment_adapter
from datetime import datetime, timezone

logger = get_logger('agent_tools')


def tool_get_payment(payment_id: int) -> dict:
    """Tool: Get payment details."""
    payment = Payment.query.get(payment_id)
    if not payment:
        return {'error': 'Payment not found'}

    customer = payment.customer
    return {
        'payment_id': payment.id,
        'amount': payment.amount,
        'failure_code': payment.failure_code,
        'failure_reason': payment.failure_reason,
        'attempt_number': payment.attempt_number,
        'payment_method': payment.payment_method,
        'created_at': payment.created_at.isoformat() if payment.created_at else None,
        'customer_id': customer.id if customer else None,
    }


def tool_get_customer_history(customer_id: int) -> dict:
    """Tool: Get customer transaction history."""
    from app.models.customer import Customer
    customer = Customer.query.get(customer_id)
    if not customer:
        return {'error': 'Customer not found'}

    return {
        'customer_id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'total_transactions': customer.total_transactions,
        'successful_transactions': customer.successful_transactions,
        'failed_transactions': customer.failed_transactions,
        'success_rate': round(customer.success_rate, 4),
        'lifetime_value': customer.lifetime_value,
    }


def tool_get_failure_context(failure_code: str, payment_id: int = None) -> dict:
    """Tool: Classify failure and get context."""
    payment = Payment.query.get(payment_id) if payment_id else None
    attempt_number = payment.attempt_number if payment else 1

    category = classify_failure(failure_code, attempt_number)

    return {
        'failure_code': failure_code,
        'failure_category': category,
        'description': {
            'TRANSIENT': 'Temporary infrastructure failure — likely recoverable',
            'CUSTOMER_FUNDS': 'Customer account balance issue — may recover later',
            'PAYMENT_METHOD': 'Payment method problem — alternate method needed',
            'ISSUER_DECLINE': 'Issuer rejection — customer authorization required',
            'REPEATED_FAILURE': 'Multiple attempts failed — stop and escalate',
            'UNKNOWN': 'Unknown failure — requires human review',
        }.get(category, 'Unknown'),
    }


def tool_predict_recovery(payment_id: int) -> dict:
    """Tool: Get ML recovery prediction."""
    payment = Payment.query.get(payment_id)
    if not payment:
        return {'error': 'Payment not found'}

    # Build feature dict for predictor
    customer = payment.customer
    feature_dict = {
        'amount': payment.amount,
        'currency': 'INR',
        'payment_method': payment.payment_method,
        'failure_code': payment.failure_code or 'unknown',
        'failure_category': classify_failure(payment.failure_code, payment.attempt_number),
        'attempt_number': payment.attempt_number,
        'customer_total_transactions': customer.total_transactions if customer else 1,
        'customer_successful_transactions': customer.successful_transactions if customer else 0,
        'customer_failed_transactions': customer.failed_transactions if customer else 0,
        'customer_success_rate': customer.success_rate if customer else 0.0,
        'customer_lifetime_value': customer.lifetime_value if customer else 0,
        'is_subscription': 0,
        'hours_since_failure': 1.0,
    }

    predictor = get_predictor()
    prediction = predictor.predict(feature_dict)

    return {
        'payment_id': payment_id,
        'recovery_probability': prediction['probability'],
        'expected_recovery': prediction['expected_recovery'],
        'model_version': prediction['model_version'],
    }


def tool_get_policy(merchant_id: int) -> dict:
    """Tool: Get merchant recovery policy."""
    from app.models.policy import Policy
    policy = Policy.query.filter_by(merchant_id=merchant_id).first()

    if policy:
        return {
            'max_retry_attempts': policy.max_retry_attempts,
            'max_auto_retry_amount': policy.max_auto_retry_amount,
            'min_recovery_probability': policy.min_recovery_probability,
            'approval_threshold': policy.approval_threshold,
            'cooldown_minutes': policy.cooldown_minutes,
        }

    # Return defaults
    return {
        'max_retry_attempts': 2,
        'max_auto_retry_amount': 1000000,
        'min_recovery_probability': 0.65,
        'approval_threshold': 1000000,
        'cooldown_minutes': 15,
    }


def tool_propose_recovery_action(action_type: str, reason: str, confidence: float) -> dict:
    """Tool: Propose an action (recommendation only, no execution)."""
    return {
        'proposed_action': action_type,
        'reason': reason,
        'confidence': round(confidence, 2),
        'status': 'PROPOSED',
        'note': 'This is a recommendation. Policy engine and human review will decide execution.',
    }


def tool_evaluate_policy(action_type: str, payment_id: int) -> dict:
    """Tool: Check if action is allowed by policy."""
    payment = Payment.query.get(payment_id)
    if not payment:
        return {'error': 'Payment not found'}

    customer = payment.customer
    recovery_case = RecoveryCase.query.filter_by(payment_id=payment_id).first()

    # Build context for policy engine
    context = {
        'action_type': action_type,
        'amount': payment.amount,
        'attempt_number': payment.attempt_number,
        'failure_category': classify_failure(payment.failure_code, payment.attempt_number),
        'recovery_probability': (
            recovery_case.recovery_probability
            if recovery_case and recovery_case.recovery_probability is not None
            else 0.5
        ),
        'confidence': (
            recovery_case.confidence
            if recovery_case and recovery_case.confidence is not None
            else 0.5
        ),
        'last_action_at': None,
        'max_retry_attempts': 2,
        'max_auto_retry_amount': 1000000,
        'min_recovery_probability': 0.65,
        'approval_threshold': 1000000,
        'cooldown_minutes': 15,
        'min_confidence_threshold': 0.60,
        'customer_email': customer.email if customer else None,
        'customer_total_transactions': customer.total_transactions if customer else 1,
        'customer_failed_transactions': customer.failed_transactions if customer else 0,
    }

    policy_engine = get_policy_engine()
    result = policy_engine.evaluate_action(action_type, context)

    return {
        'allowed': result.allowed,
        'requires_approval': result.requires_approval,
        'reason': result.reason,
        'details': [r['reason'] for r in result.rule_results],
    }


def tool_execute_retry(recovery_case_id: int, reason: str) -> dict:
    """Tool: Execute a retry action (privileged—only after policy approval)."""
    case = RecoveryCase.query.get(recovery_case_id)
    if not case:
        return {'error': 'Recovery case not found'}

    payment = case.payment
    if not payment:
        return {'error': 'Payment not found'}

    # Log the execution attempt
    AuditService.log(
        entity_type='recovery_case',
        entity_id=recovery_case_id,
        event_type='RETRY_EXECUTED',
        actor='RecoverAI Agent',
        action=f'Retry executed via payment adapter',
        input_summary={'reason': reason},
    )

    # Attempt recovery via payment adapter
    adapter = get_payment_adapter()
    result = adapter.attempt_recovery(
        payment_id=f'pay_{payment.id}',
        amount=payment.amount,
        recovery_probability=case.recovery_probability or 0.5,
    )

    if result.get('success') and result.get('recovered'):
        case.status = 'RECOVERED'
        action = RecoveryAction(
            recovery_case_id=recovery_case_id,
            action_type='RETRY',
            status='SUCCESSFUL',
            reason=reason,
            recovered_amount=payment.amount,
            result=result,
        )
        db.session.add(action)
        db.session.commit()

        return {
            'status': 'SUCCESS',
            'recovered': True,
            'amount': payment.amount,
            'message': 'Payment recovered successfully',
        }
    else:
        case.status = 'FAILED'
        action = RecoveryAction(
            recovery_case_id=recovery_case_id,
            action_type='RETRY',
            status='FAILED',
            reason=reason,
            result=result,
        )
        db.session.add(action)
        db.session.commit()

        return {
            'status': 'FAILED',
            'recovered': False,
            'message': 'Recovery attempt failed',
        }


def tool_send_recovery_notification(recovery_case_id: int, message: str, channel: str = 'email') -> dict:
    """Tool: Send customer notification."""
    case = RecoveryCase.query.get(recovery_case_id)
    if not case:
        return {'error': 'Recovery case not found'}

    payment = case.payment
    customer = payment.customer if payment else None
    if not customer:
        return {'error': 'Customer not found'}

    result = NotificationService.send_recovery_notification(
        customer, payment, case, channel=channel
    )

    action = RecoveryAction(
        recovery_case_id=recovery_case_id,
        action_type='NOTIFY_CUSTOMER',
        status='EXECUTED',
        reason=f'Notification sent via {channel}',
        result={'channel': channel, 'message': message, 'simulated': True},
    )
    db.session.add(action)
    db.session.commit()

    return result


def tool_escalate_case(recovery_case_id: int, reason: str) -> dict:
    """Tool: Escalate case to human review."""
    case = RecoveryCase.query.get(recovery_case_id)
    if not case:
        return {'error': 'Recovery case not found'}

    case.status = 'ESCALATED'

    action = RecoveryAction(
        recovery_case_id=recovery_case_id,
        action_type='ESCALATE',
        status='EXECUTED',
        reason=reason,
    )
    db.session.add(action)

    AuditService.log(
        entity_type='recovery_case',
        entity_id=recovery_case_id,
        event_type='ESCALATED',
        actor='RecoverAI Agent',
        action='Case escalated to human review',
        input_summary={'reason': reason},
    )

    db.session.commit()

    return {
        'status': 'ESCALATED',
        'reason': reason,
        'message': 'Case marked for human review',
    }


# Tool dispatch
TOOLS = {
    'get_payment': tool_get_payment,
    'get_customer_history': tool_get_customer_history,
    'get_failure_context': tool_get_failure_context,
    'predict_recovery': tool_predict_recovery,
    'get_policy': tool_get_policy,
    'propose_recovery_action': tool_propose_recovery_action,
    'evaluate_policy': tool_evaluate_policy,
    'execute_retry': tool_execute_retry,
    'send_recovery_notification': tool_send_recovery_notification,
    'escalate_case': tool_escalate_case,
}


def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    """Dispatch a tool call."""
    if tool_name not in TOOLS:
        return {'error': f'Unknown tool: {tool_name}'}

    try:
        return TOOLS[tool_name](**tool_input)
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return {'error': str(e)}
