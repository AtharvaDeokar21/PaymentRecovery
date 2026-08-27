"""Demo mode endpoints for running deterministic scenarios."""

from flask import Blueprint, jsonify, current_app
from app import db
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.payment_event import PaymentEvent
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.agent_decision import AgentDecision
from app.models.audit_log import AuditLog
from app.models.policy import Policy
from app.seed.scenarios import SCENARIOS
from app.seed.seed_data import seed_database, clear_database
from app.utils.logging import get_logger
from app.utils.helpers import utcnow

logger = get_logger('demo')

demo_bp = Blueprint('demo', __name__)


@demo_bp.route('/reset', methods=['POST'])
def demo_reset():
    """Reset database to initial state."""
    try:
        clear_database()
        seed_database()
        logger.info("Demo database reset successfully")
        return jsonify({
            'status': 'reset',
            'message': 'Database reset to initial state',
            'scenario_count': len(SCENARIOS),
        })
    except Exception as e:
        logger.error(f"Demo reset failed: {e}")
        return jsonify({'error': str(e)}), 500


@demo_bp.route('/run', methods=['POST'])
def demo_run():
    """Run the complete demo with all scenarios."""
    try:
        logger.info("Starting demo run...")

        # Get or create merchant
        merchant = Merchant.query.first()
        if not merchant:
            merchant = Merchant(
                name='Demo Merchant',
                email='demo@example.com',
                currency='INR',
            )
            db.session.add(merchant)
            db.session.flush()

        results = []

        # Run each scenario
        for scenario in SCENARIOS:
            logger.info(f"Running scenario {scenario['id']}: {scenario['name']}")
            result = _run_scenario(merchant, scenario)
            results.append(result)

        db.session.commit()
        logger.info("Demo run completed successfully")

        return jsonify({
            'status': 'completed',
            'message': 'Demo scenarios executed',
            'scenarios': results,
            'total_scenarios': len(results),
        })

    except Exception as e:
        logger.error(f"Demo run failed: {e}")
        return jsonify({'error': str(e)}), 500


def _run_scenario(merchant, scenario: dict) -> dict:
    """Run a single demo scenario."""
    scenario_id = scenario['id']

    try:
        # Create customer
        cust_data = scenario['customer']
        customer = Customer(
            merchant_id=merchant.id,
            external_customer_id=f'cust_demo_{scenario_id}',
            name=cust_data['name'],
            email=cust_data['email'],
            phone=cust_data.get('phone'),
            total_transactions=cust_data['total_transactions'],
            successful_transactions=cust_data['successful_transactions'],
            failed_transactions=cust_data['failed_transactions'],
            lifetime_value=cust_data['lifetime_value'],
        )
        db.session.add(customer)
        db.session.flush()

        # Create payment
        payment_data = scenario['payment']
        payment = Payment(
            merchant_id=merchant.id,
            customer_id=customer.id,
            razorpay_order_id=f'order_demo_{scenario_id}',
            razorpay_payment_id=f'pay_demo_{scenario_id}',
            amount=payment_data['amount'],
            currency=payment_data['currency'],
            payment_method=payment_data['payment_method'],
            status='failed',
            failure_code=payment_data['failure_code'],
            failure_reason=payment_data['failure_reason'],
            attempt_number=payment_data['attempt_number'],
        )
        db.session.add(payment)
        db.session.flush()

        # Create payment event
        event = PaymentEvent(
            payment_id=payment.id,
            event_type='payment.failed',
            event_data={
                'failure_code': payment.failure_code,
                'amount': payment.amount,
            },
        )
        db.session.add(event)

        # Create recovery case
        expected = scenario['expected_outcome']
        case = RecoveryCase(
            payment_id=payment.id,
            status='DETECTED',
            revenue_at_risk=payment.amount,
            priority='HIGH' if payment.amount > 1000000 else 'MEDIUM',
        )
        db.session.add(case)
        db.session.flush()

        # Simulate recovery analysis (would be done by agent in real scenario)
        # For demo, we just set expected outcomes
        case.recovery_probability = expected.get('recovery_probability_min', 0.5)
        case.expected_recovery = int(payment.amount * case.recovery_probability)
        case.recommended_action = expected['recommended_action']
        case.diagnosis = f"Scenario {scenario_id}: {scenario['description']}"
        case.confidence = expected.get('recovery_probability_min', 0.5)

        # Create mock decision
        decision = AgentDecision(
            recovery_case_id=case.id,
            diagnosis=f"Category from scenario",
            reasoning_summary=scenario['description'],
            confidence=case.confidence,
            recommended_action=case.recommended_action,
            tool_calls=[],
        )
        db.session.add(decision)

        # Simulate final status
        if scenario_id == 'A':
            # Successful recovery
            case.status = 'RECOVERED'
            action = RecoveryAction(
                recovery_case_id=case.id,
                action_type='RETRY',
                status='SUCCESSFUL',
                reason='Gateway timeout resolved on retry',
                recovered_amount=payment.amount,
                result={'recovered': True},
            )
            db.session.add(action)

            audit = AuditLog(
                entity_type='recovery_case',
                entity_id=case.id,
                event_type='RECOVERED',
                actor='RecoverAI Agent',
                action='Payment recovered via retry',
                output_summary={'amount_recovered': payment.amount},
            )
            db.session.add(audit)

        elif scenario_id in ['C', 'D', 'E']:
            # Escalated
            case.status = 'ESCALATED'
            action = RecoveryAction(
                recovery_case_id=case.id,
                action_type='ESCALATE',
                status='EXECUTED',
                reason=scenario['description'],
                result={'escalated': True},
            )
            db.session.add(action)

            audit = AuditLog(
                entity_type='recovery_case',
                entity_id=case.id,
                event_type='ESCALATED',
                actor='RecoverAI Agent',
                action=f'Escalated: {scenario["description"]}',
            )
            db.session.add(audit)

        elif scenario_id == 'B':
            # Action pending (notification)
            case.status = 'ACTION_PENDING'
            action = RecoveryAction(
                recovery_case_id=case.id,
                action_type='NOTIFY_CUSTOMER',
                status='EXECUTED',
                reason='Insufficient funds — customer notification sent',
                result={'notified': True},
            )
            db.session.add(action)

        db.session.commit()

        return {
            'scenario_id': scenario_id,
            'name': scenario['name'],
            'payment_id': payment.id,
            'case_id': case.id,
            'final_status': case.status,
            'amount': payment.amount,
            'customer': customer.name,
        }

    except Exception as e:
        logger.error(f"Scenario {scenario_id} failed: {e}")
        db.session.rollback()
        return {
            'scenario_id': scenario_id,
            'error': str(e),
        }
