"""Generate synthetic payment dataset for ML training."""

import random
import csv
import os
from datetime import datetime, timedelta

# Seed for reproducibility
random.seed(42)

FAILURE_CODES = {
    'TRANSIENT': ['gateway_timeout', 'network_error', 'temporary_bank_unavailable', 'processing_timeout'],
    'CUSTOMER_FUNDS': ['insufficient_funds', 'limit_exceeded'],
    'PAYMENT_METHOD': ['expired_card', 'invalid_card', 'unsupported_method'],
    'ISSUER_DECLINE': ['issuer_declined', 'do_not_honor'],
    'UNKNOWN': ['internal_error', 'unclassified_error'],
}

PAYMENT_METHODS = ['card', 'netbanking', 'upi', 'wallet', 'emi']

# Recovery probabilities by category (base rates)
BASE_RECOVERY_RATES = {
    'TRANSIENT': 0.72,
    'CUSTOMER_FUNDS': 0.25,
    'PAYMENT_METHOD': 0.15,
    'ISSUER_DECLINE': 0.20,
    'UNKNOWN': 0.10,
}


def generate_customer():
    """Generate a synthetic customer profile."""
    total_txn = random.randint(1, 50)
    success_rate = random.betavariate(5, 2)  # skewed toward success
    successful = int(total_txn * success_rate)
    failed = total_txn - successful
    ltv = successful * random.randint(50000, 500000)  # paise

    return {
        'total_transactions': total_txn,
        'successful_transactions': successful,
        'failed_transactions': failed,
        'success_rate': round(success_rate, 4),
        'lifetime_value': ltv,
    }


def generate_record(record_id):
    """Generate a single synthetic payment record."""
    # Pick failure category with realistic distribution
    category_weights = {
        'TRANSIENT': 0.35,
        'CUSTOMER_FUNDS': 0.25,
        'PAYMENT_METHOD': 0.15,
        'ISSUER_DECLINE': 0.15,
        'UNKNOWN': 0.10,
    }
    category = random.choices(
        list(category_weights.keys()),
        weights=list(category_weights.values()),
        k=1
    )[0]
    failure_code = random.choice(FAILURE_CODES[category])

    payment_method = random.choice(PAYMENT_METHODS)
    amount = random.choice([
        random.randint(10000, 100000),    # ₹100 - ₹1,000
        random.randint(100000, 500000),   # ₹1,000 - ₹5,000
        random.randint(500000, 2000000),  # ₹5,000 - ₹20,000
        random.randint(2000000, 5000000), # ₹20,000 - ₹50,000
    ])

    attempt_number = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05], k=1)[0]
    customer = generate_customer()

    is_subscription = random.random() < 0.3
    hours_since_failure = random.uniform(0.1, 72)

    # Calculate recovery probability based on features
    base_prob = BASE_RECOVERY_RATES[category]

    # Adjust based on features
    prob = base_prob

    # Customer history boost
    if customer['success_rate'] > 0.8:
        prob += 0.12
    elif customer['success_rate'] > 0.6:
        prob += 0.05
    elif customer['success_rate'] < 0.3:
        prob -= 0.10

    # Attempt penalty
    if attempt_number >= 3:
        prob -= 0.25
    elif attempt_number == 2:
        prob -= 0.10

    # Amount factor
    if amount > 2000000:  # > ₹20,000
        prob -= 0.05
    elif amount < 100000:  # < ₹1,000
        prob += 0.05

    # Time factor
    if hours_since_failure > 48:
        prob -= 0.15
    elif hours_since_failure < 1:
        prob += 0.08

    # Subscription boost
    if is_subscription:
        prob += 0.05

    # LTV boost
    if customer['lifetime_value'] > 5000000:  # > ₹50K
        prob += 0.05

    # Clamp and add noise
    prob = max(0.02, min(0.98, prob))
    prob += random.gauss(0, 0.05)
    prob = max(0.01, min(0.99, prob))

    # Determine outcome with the probability
    recovered = 1 if random.random() < prob else 0

    return {
        'record_id': record_id,
        'amount': amount,
        'currency': 'INR',
        'payment_method': payment_method,
        'failure_code': failure_code,
        'failure_category': category,
        'attempt_number': attempt_number,
        'customer_total_transactions': customer['total_transactions'],
        'customer_successful_transactions': customer['successful_transactions'],
        'customer_failed_transactions': customer['failed_transactions'],
        'customer_success_rate': customer['success_rate'],
        'customer_lifetime_value': customer['lifetime_value'],
        'is_subscription': int(is_subscription),
        'hours_since_failure': round(hours_since_failure, 2),
        'recovered': recovered,
        'recovery_probability': round(prob, 4),
    }


def generate_dataset(n_records=12000, output_dir=None):
    """Generate the full synthetic dataset."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, 'synthetic_payments.csv')
    records = [generate_record(i) for i in range(n_records)]

    fieldnames = list(records[0].keys())
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # Print summary
    total = len(records)
    recovered = sum(1 for r in records if r['recovered'] == 1)
    print(f"Generated {total} records → {filepath}")
    print(f"  Recovered: {recovered} ({recovered/total*100:.1f}%)")
    print(f"  Failed:    {total - recovered} ({(total-recovered)/total*100:.1f}%)")

    return filepath


if __name__ == '__main__':
    generate_dataset()
