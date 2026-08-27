"""Seed the database with merchants, customers, payments for demo."""

import random
from datetime import datetime, timedelta, timezone

random.seed(42)

from app import db
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.payment_event import PaymentEvent
from app.models.recovery_case import RecoveryCase
from app.models.policy import Policy
from app.utils.helpers import classify_failure

FIRST_NAMES = [
    'Aarav', 'Aditi', 'Aisha', 'Amit', 'Ananya', 'Arjun', 'Deepa', 'Dev',
    'Diya', 'Gaurav', 'Isha', 'Kabir', 'Kavya', 'Krishna', 'Lakshmi',
    'Manish', 'Meera', 'Nisha', 'Pooja', 'Raj', 'Riya', 'Rohan', 'Sanya',
    'Siddharth', 'Sneha', 'Suresh', 'Tanvi', 'Varun', 'Vidya', 'Yash',
]

LAST_NAMES = [
    'Agarwal', 'Bhat', 'Chauhan', 'Desai', 'Gupta', 'Iyer', 'Jain',
    'Kapoor', 'Kumar', 'Malhotra', 'Nair', 'Patel', 'Rao', 'Reddy',
    'Shah', 'Sharma', 'Singh', 'Srinivasan', 'Verma', 'Yadav',
]

FAILURE_CODES = [
    'gateway_timeout', 'network_error', 'temporary_bank_unavailable',
    'processing_timeout', 'insufficient_funds', 'limit_exceeded',
    'expired_card', 'invalid_card', 'unsupported_method',
    'issuer_declined', 'do_not_honor',
]

PAYMENT_METHODS = ['card', 'netbanking', 'upi', 'wallet', 'emi']


def seed_database():
    """Seed database with demo data."""
    print("Seeding database...")

    # Create merchant
    merchant = Merchant.query.first()
    if not merchant:
        merchant = Merchant(
            name='TechMart India',
            email='admin@techmart.in',
            currency='INR',
        )
        db.session.add(merchant)
        db.session.flush()

    # Create policy
    policy = Policy.query.filter_by(merchant_id=merchant.id).first()
    if not policy:
        policy = Policy(
            merchant_id=merchant.id,
            max_retry_attempts=2,
            max_auto_retry_amount=1000000,  # ₹10,000 in paise
            min_recovery_probability=0.65,
            approval_threshold=1000000,  # ₹10,000 in paise
            cooldown_minutes=15,
        )
        db.session.add(policy)
        db.session.flush()

    # Create 200 customers
    customers = []
    for i in range(200):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        total_txn = random.randint(2, 30)
        success_rate = random.betavariate(5, 2)
        successful = max(1, int(total_txn * success_rate))
        failed = total_txn - successful

        customer = Customer(
            merchant_id=merchant.id,
            external_customer_id=f'cust_{i+1:04d}',
            name=f'{first} {last}',
            email=f'{first.lower()}.{last.lower()}{i}@example.com',
            phone=f'+91987654{random.randint(1000, 9999)}',
            total_transactions=total_txn,
            successful_transactions=successful,
            failed_transactions=failed,
            lifetime_value=successful * random.randint(50000, 300000),
        )
        customers.append(customer)
        db.session.add(customer)

    db.session.flush()

    # Create 200 failed payments → recovery cases
    now = datetime.now(timezone.utc)
    for i in range(200):
        customer = random.choice(customers)
        amount = random.choice([
            random.randint(50000, 200000),
            random.randint(200000, 500000),
            random.randint(500000, 1500000),
            random.randint(1500000, 3000000),
        ])
        failure_code = random.choice(FAILURE_CODES)
        attempt_number = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1], k=1)[0]
        created_at = now - timedelta(hours=random.uniform(0.5, 48))

        payment = Payment(
            merchant_id=merchant.id,
            customer_id=customer.id,
            razorpay_order_id=f'order_RP{10000+i}',
            razorpay_payment_id=f'pay_RP{10000+i}',
            amount=amount,
            currency='INR',
            payment_method=random.choice(PAYMENT_METHODS),
            status='failed',
            failure_code=failure_code,
            failure_reason=f'Payment failed due to {failure_code.replace("_", " ")}',
            attempt_number=attempt_number,
            created_at=created_at,
        )
        db.session.add(payment)
        db.session.flush()

        # Create payment event
        event = PaymentEvent(
            payment_id=payment.id,
            event_type='payment.failed',
            event_data={
                'failure_code': failure_code,
                'amount': amount,
                'method': payment.payment_method,
            },
            timestamp=created_at,
        )
        db.session.add(event)

        # Create recovery case
        category = classify_failure(failure_code, attempt_number)
        case = RecoveryCase(
            payment_id=payment.id,
            status='DETECTED',
            revenue_at_risk=amount,
            priority='HIGH' if amount > 1000000 else 'MEDIUM',
            created_at=created_at,
        )
        db.session.add(case)

    db.session.commit()
    print(f"Seeded: 1 merchant, {len(customers)} customers, 200 payments, 200 recovery cases")


def clear_database():
    """Clear all demo data."""
    print("Clearing database...")
    from app.models.audit_log import AuditLog
    from app.models.agent_decision import AgentDecision
    from app.models.recovery_action import RecoveryAction

    AuditLog.query.delete()
    AgentDecision.query.delete()
    RecoveryAction.query.delete()
    RecoveryCase.query.delete()
    PaymentEvent.query.delete()
    Payment.query.delete()
    Customer.query.delete()
    Policy.query.delete()
    Merchant.query.delete()
    db.session.commit()
    print("Database cleared.")


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_database()
