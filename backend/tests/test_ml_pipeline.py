"""Test ML pipeline components."""

import pytest
import pandas as pd
from app.ml.features import extract_features, prepare_dataset
from app.ml.predictor import RecoveryPredictor, get_predictor


@pytest.fixture
def sample_payment():
    """Sample payment data for testing."""
    return {
        'amount': 500000,
        'currency': 'INR',
        'payment_method': 'card',
        'failure_code': 'gateway_timeout',
        'failure_category': 'TRANSIENT',
        'attempt_number': 1,
        'customer_total_transactions': 10,
        'customer_successful_transactions': 8,
        'customer_failed_transactions': 2,
        'customer_success_rate': 0.8,
        'customer_lifetime_value': 2000000,
        'is_subscription': 0,
        'hours_since_failure': 1.0,
    }


def test_predictor_singleton():
    """Test predictor singleton pattern."""
    p1 = get_predictor()
    p2 = get_predictor()
    assert p1 is p2


def test_predictor_fallback_mode(sample_payment):
    """Test predictor returns fallback when model unavailable."""
    predictor = RecoveryPredictor()
    predictor.model = None  # Simulate missing model

    result = predictor.predict(sample_payment)
    assert result['probability'] == 0.35  # Fallback
    assert result['model_version'] == 'baseline'


def test_predictor_returns_valid_range(sample_payment):
    """Test predictor returns probability in valid range."""
    predictor = RecoveryPredictor()
    result = predictor.predict(sample_payment)

    assert 0.0 <= result['probability'] <= 1.0
    assert result['expected_recovery'] >= 0
    assert isinstance(result['model_version'], str)


def test_feature_extraction():
    """Test feature extraction process."""
    df = pd.DataFrame([{
        'amount': 500000,
        'currency': 'INR',
        'payment_method': 'card',
        'failure_code': 'gateway_timeout',
        'failure_category': 'TRANSIENT',
        'attempt_number': 1,
        'customer_total_transactions': 10,
        'customer_successful_transactions': 8,
        'customer_failed_transactions': 2,
        'customer_success_rate': 0.8,
        'customer_lifetime_value': 2000000,
        'is_subscription': 0,
        'hours_since_failure': 1.0,
        'recovered': 1,
    }])

    features = extract_features(df)

    # Should have more features than input (due to encoding)
    assert features.shape[1] > df.shape[1]
    # Should have derived features
    assert 'amount_normalized' in features.columns
    assert 'ltv_normalized' in features.columns
    assert 'failure_rate' in features.columns
