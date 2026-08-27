"""Feature engineering for recovery prediction model."""

import pandas as pd
import numpy as np


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and engineer features from raw payment data."""
    features = df.copy()

    # Numeric features (already present)
    numeric_cols = [
        'amount',
        'attempt_number',
        'customer_total_transactions',
        'customer_successful_transactions',
        'customer_failed_transactions',
        'customer_success_rate',
        'customer_lifetime_value',
        'hours_since_failure',
    ]

    # Binary features
    features['is_subscription'] = features['is_subscription'].astype(int)

    # Categorical encoding - payment_method
    payment_method_dummies = pd.get_dummies(features['payment_method'], prefix='method')
    features = pd.concat([features, payment_method_dummies], axis=1)

    # Categorical encoding - failure_category
    category_dummies = pd.get_dummies(features['failure_category'], prefix='category')
    features = pd.concat([features, category_dummies], axis=1)

    # Derived features
    features['amount_normalized'] = np.log1p(features['amount'])
    features['ltv_normalized'] = np.log1p(features['customer_lifetime_value'])
    features['failure_rate'] = features['customer_failed_transactions'] / features['customer_total_transactions'].clip(lower=1)
    features['high_value'] = (features['amount'] > 1000000).astype(int)  # > ₹10,000
    features['high_ltv'] = (features['customer_lifetime_value'] > 5000000).astype(int)  # > ₹50,000
    features['repeat_failure'] = (features['attempt_number'] >= 3).astype(int)
    features['time_decay'] = np.exp(-features['hours_since_failure'] / 24.0)

    # Drop original categorical columns and non-feature columns
    drop_cols = ['record_id', 'currency', 'payment_method', 'failure_code', 'failure_category', 'recovery_probability']
    features = features.drop(columns=[c for c in drop_cols if c in features.columns], errors='ignore')

    return features


def get_feature_names() -> list:
    """Return expected feature column names in order."""
    base_features = [
        'amount',
        'attempt_number',
        'customer_total_transactions',
        'customer_successful_transactions',
        'customer_failed_transactions',
        'customer_success_rate',
        'customer_lifetime_value',
        'is_subscription',
        'hours_since_failure',
    ]

    # Derived features
    derived = [
        'amount_normalized',
        'ltv_normalized',
        'failure_rate',
        'high_value',
        'high_ltv',
        'repeat_failure',
        'time_decay',
    ]

    # Payment method dummies
    payment_methods = ['card', 'emi', 'netbanking', 'upi', 'wallet']
    method_features = [f'method_{m}' for m in payment_methods]

    # Category dummies
    categories = ['CUSTOMER_FUNDS', 'ISSUER_DECLINE', 'PAYMENT_METHOD', 'TRANSIENT', 'UNKNOWN']
    category_features = [f'category_{c}' for c in categories]

    return base_features + derived + method_features + category_features


def prepare_dataset(filepath: str):
    """Load and prepare the dataset for training."""
    df = pd.read_csv(filepath)

    # Extract features
    X = extract_features(df)
    y = df['recovered'].values

    return X, y
