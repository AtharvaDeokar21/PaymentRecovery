"""Analytics endpoints for recovery metrics and baselines."""

from flask import Blueprint, jsonify
from app import db
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/recovery-over-time')
def recovery_over_time():
    """Recovery revenue over time."""
    results = db.session.query(
        func.date(RecoveryCase.created_at).label('date'),
        func.count(RecoveryCase.id).label('cases'),
        func.sum(RecoveryCase.revenue_at_risk).label('revenue_at_risk'),
        func.sum(RecoveryCase.expected_recovery).label('recovered'),
    ).filter(
        RecoveryCase.status == 'RECOVERED'
    ).group_by(
        func.date(RecoveryCase.created_at)
    ).order_by(
        'date'
    ).all()

    return jsonify({
        'timeline': [
            {
                'date': str(r[0]),
                'cases': r[1],
                'revenue_at_risk': r[2] or 0,
                'recovered': r[3] or 0,
            }
            for r in results
        ]
    })


@analytics_bp.route('/by-failure-type')
def by_failure_type():
    """Recovery breakdown by failure type."""
    from app.utils.helpers import classify_failure

    payments = Payment.query.filter_by(status='failed').all()
    by_type = {}

    for p in payments:
        cat = classify_failure(p.failure_code, p.attempt_number)
        if cat not in by_type:
            by_type[cat] = {'cases': 0, 'revenue': 0, 'recovered': 0}
        by_type[cat]['cases'] += 1
        by_type[cat]['revenue'] += p.amount

        case = p.recovery_case
        if case and case.status == 'RECOVERED':
            by_type[cat]['recovered'] += case.expected_recovery or 0

    return jsonify({
        'by_failure_type': [
            {
                'type': k,
                'cases': v['cases'],
                'revenue_at_risk': v['revenue'],
                'recovered': v['recovered'],
            }
            for k, v in sorted(by_type.items())
        ]
    })


@analytics_bp.route('/by-payment-method')
def by_payment_method():
    """Recovery breakdown by payment method."""
    results = db.session.query(
        Payment.payment_method,
        func.count(Payment.id).label('total'),
        func.sum(Payment.amount).label('total_amount'),
    ).filter(
        Payment.status == 'failed'
    ).group_by(
        Payment.payment_method
    ).all()

    return jsonify({
        'by_method': [
            {
                'method': r[0] or 'unknown',
                'cases': r[1],
                'amount': r[2] or 0,
            }
            for r in results
        ]
    })


@analytics_bp.route('/baseline-comparison')
def baseline_comparison():
    """Compare AI recovery vs. baseline naive strategy."""
    total_failed = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'failed'
    ).scalar() or 0

    ai_recovered = db.session.query(func.sum(RecoveryAction.recovered_amount)).filter(
        RecoveryAction.status == 'SUCCESSFUL'
    ).scalar() or 0

    # Baseline: retry everything once, ~27% recovery rate
    baseline_recovered = int(total_failed * 0.272)

    ai_recovery_rate = (ai_recovered / total_failed * 100) if total_failed > 0 else 0
    baseline_recovery_rate = (baseline_recovered / total_failed * 100) if total_failed > 0 else 0

    incremental = max(0, ai_recovered - baseline_recovered)
    uplift = ((ai_recovered - baseline_recovered) / baseline_recovered * 100) if baseline_recovered > 0 else 0

    return jsonify({
        'total_failed': total_failed,
        'baseline': {
            'name': 'Naive Retry',
            'strategy': 'Retry every failed payment once',
            'recovered': baseline_recovered,
            'recovery_rate': round(baseline_recovery_rate, 1),
            'actions': int(total_failed * 0.5),  # Assume 50% retry
            'unnecessary_actions': int(total_failed * 0.15),
        },
        'ai_recoverai': {
            'name': 'RecoverAI',
            'strategy': 'ML + agent + policy + selective recovery',
            'recovered': ai_recovered,
            'recovery_rate': round(ai_recovery_rate, 1),
            'actions': db.session.query(func.count(RecoveryAction.id)).scalar(),
            'unnecessary_actions': db.session.query(func.count(RecoveryAction.id)).filter(
                RecoveryAction.status == 'BLOCKED'
            ).scalar() or 0,
        },
        'incremental_recovery': incremental,
        'recovery_uplift_percent': round(uplift, 1),
    })


@analytics_bp.route('/action-distribution')
def action_distribution():
    """Distribution of recovery actions taken."""
    results = db.session.query(
        RecoveryAction.action_type,
        func.count(RecoveryAction.id).label('count'),
    ).group_by(
        RecoveryAction.action_type
    ).all()

    return jsonify({
        'actions': [
            {'type': r[0], 'count': r[1]}
            for r in results
        ]
    })
