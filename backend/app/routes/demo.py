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
    """Run a single demo scenario using the real RecoveryAgent pipeline."""
    scenario_id = scenario['id']

    try:
        logger.info(f"========== SCENARIO {scenario_id} START ==========")

        # 1. Create customer
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
        logger.info(f"Created customer: {customer.id} ({customer.name})")

        # 2. Create payment
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
        logger.info(f"Created payment: {payment.id} (amount={payment.amount} paise)")

        # 3. Create payment event
        event = PaymentEvent(
            payment_id=payment.id,
            event_type='payment.failed',
            event_data={
                'failure_code': payment.failure_code,
                'amount': payment.amount,
            },
        )
        db.session.add(event)
        db.session.flush()
        logger.info(f"Created payment event for failure code: {payment.failure_code}")

        # 4. Create recovery case (DETECTED status - waiting for analysis)
        case = RecoveryCase(
            payment_id=payment.id,
            status='DETECTED',
            revenue_at_risk=payment.amount,
            priority='HIGH' if payment.amount > 1000000 else 'MEDIUM',
        )
        db.session.add(case)
        db.session.flush()
        logger.info(f"Created recovery case: {case.id} (status=DETECTED, priority={case.priority})")

        db.session.commit()

        # 5. Invoke the REAL RecoveryAgent to analyze the case
        logger.info(f"Invoking RecoveryAgent.analyze({case.id})...")
        from app.agent.recovery_agent import RecoveryAgent
        agent = RecoveryAgent()
        agent_result = agent.analyze(case.id)

        # Refresh case from DB to get updates made by agent
        db.session.refresh(case)

        logger.info(f"Agent analysis complete. Case status: {case.status}")
        logger.info(f"Recommended action: {case.recommended_action}")
        logger.info(f"Recovery probability: {case.recovery_probability}")

        # Check if agent hit an error
        if agent_result.get('error'):
            logger.error(f"Agent analysis failed: {agent_result['error']}")
            case.status = 'FAILED'
            db.session.commit()
            return {
                'scenario_id': scenario_id,
                'name': scenario['name'],
                'payment_id': payment.id,
                'case_id': case.id,
                'final_status': 'FAILED',
                'amount': payment.amount,
                'customer': customer.name,
                'error': agent_result.get('error'),
            }

        # 6. Get latest agent decision to report
        decisions = AgentDecision.query.filter_by(recovery_case_id=case.id).all()
        latest_decision = decisions[-1] if decisions else None

        logger.info(f"========== SCENARIO {scenario_id} END ==========")
        logger.info(f"Final case status: {case.status}")

        return {
            'scenario_id': scenario_id,
            'name': scenario['name'],
            'description': scenario['description'],
            'payment_id': payment.id,
            'case_id': case.id,
            'customer_name': customer.name,
            'amount': payment.amount,
            'failure_code': payment.failure_code,
            'final_status': case.status,
            'diagnosis': case.diagnosis,
            'recommended_action': case.recommended_action,
            'recovery_probability': case.recovery_probability,
            'expected_recovery': case.expected_recovery,
            'confidence': case.confidence,
            'agent_decision_id': latest_decision.id if latest_decision else None,
            'tool_calls_count': len(latest_decision.tool_calls) if latest_decision and latest_decision.tool_calls else 0,
        }

    except Exception as e:
        logger.error(f"Scenario {scenario_id} failed with exception: {e}", exc_info=True)
        db.session.rollback()
        return {
            'scenario_id': scenario_id,
            'name': scenario.get('name', 'Unknown'),
            'error': str(e),
        }
