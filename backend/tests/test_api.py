"""Test API endpoints."""

import pytest
from app import create_app, db
from app.models import Merchant, Customer, Payment, RecoveryCase
from app.seed.seed_data import seed_database, clear_database


@pytest.fixture
def client():
    """Create Flask test client."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        seed_database()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_health_check(client):
    """Test health endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'


def test_dashboard_summary(client):
    """Test dashboard summary endpoint."""
    response = client.get('/api/dashboard/summary')
    assert response.status_code == 200
    data = response.json
    assert 'revenue_at_risk' in data
    assert 'recovered_revenue' in data
    assert 'recovery_rate' in data


def test_dashboard_funnel(client):
    """Test recovery funnel endpoint."""
    response = client.get('/api/dashboard/funnel')
    assert response.status_code == 200
    data = response.json
    assert 'stages' in data
    assert len(data['stages']) > 0


def test_dashboard_failures(client):
    """Test failure distribution endpoint."""
    response = client.get('/api/dashboard/failures')
    assert response.status_code == 200
    data = response.json
    assert 'distribution' in data


def test_list_payments(client):
    """Test payments listing."""
    response = client.get('/api/payments')
    assert response.status_code == 200
    data = response.json
    assert 'payments' in data
    assert 'total' in data
    assert 'page' in data


def test_get_payment(client):
    """Test payment detail endpoint."""
    # Get a payment ID from the database
    with client.application.app_context():
        payment = Payment.query.first()
        if payment:
            response = client.get(f'/api/payments/{payment.id}')
            assert response.status_code == 200
            assert response.json['id'] == payment.id


def test_list_recovery_cases(client):
    """Test recovery cases listing."""
    response = client.get('/api/recovery/cases')
    assert response.status_code == 200
    data = response.json
    assert 'cases' in data
    assert 'total' in data


def test_get_recovery_case(client):
    """Test recovery case detail."""
    with client.application.app_context():
        case = RecoveryCase.query.first()
        if case:
            response = client.get(f'/api/recovery/cases/{case.id}')
            assert response.status_code == 200
            assert response.json['id'] == case.id


def test_list_audit_logs(client):
    """Test audit logs listing."""
    response = client.get('/api/audit')
    assert response.status_code == 200
    data = response.json
    assert 'logs' in data


def test_razorpay_status(client):
    """Test Razorpay status endpoint."""
    response = client.get('/api/razorpay/status')
    assert response.status_code == 200
    data = response.json
    assert 'mode' in data
    assert data['mode'] in ['test', 'simulation']


def test_get_policies(client):
    """Test policies endpoint."""
    response = client.get('/api/policies')
    assert response.status_code == 200
    data = response.json
    assert 'max_retry_attempts' in data
    assert 'max_auto_retry_amount' in data


def test_demo_reset(client):
    """Test demo reset endpoint."""
    response = client.post('/api/demo/reset')
    assert response.status_code == 200
    data = response.json
    assert data['status'] == 'reset'


def test_demo_run(client):
    """Test demo run endpoint."""
    response = client.post('/api/demo/run')
    assert response.status_code == 200
    data = response.json
    assert data['status'] == 'completed'
    assert len(data.get('scenarios', [])) > 0
