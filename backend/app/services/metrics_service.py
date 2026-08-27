from app import db
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from sqlalchemy import func


class MetricsService:
    @staticmethod
    def get_dashboard_summary():
        total_failed = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'failed'
        ).scalar() or 0
        total_failed = int(total_failed) if total_failed else 0

        recovered = db.session.query(func.sum(RecoveryAction.recovered_amount)).filter(
            RecoveryAction.status == 'SUCCESSFUL'
        ).scalar() or 0
        recovered = int(recovered) if recovered else 0

        total_cases = RecoveryCase.query.count()
        recovered_cases = RecoveryCase.query.filter_by(status='RECOVERED').count()
        active_cases = RecoveryCase.query.filter(
            RecoveryCase.status.in_(['DETECTED', 'ANALYZING', 'ACTION_PENDING', 'EXECUTING'])
        ).count()
        blocked = RecoveryCase.query.filter_by(status='BLOCKED').count()

        recovery_rate = (recovered_cases / total_cases * 100) if total_cases > 0 else 0

        # Baseline: naive retry everything once recovers ~27%
        baseline_recovered = int(total_failed * 0.272)
        incremental = max(0, recovered - baseline_recovered)

        return {
            'revenue_at_risk': total_failed,
            'recovered_revenue': recovered,
            'recovery_rate': round(recovery_rate, 1),
            'incremental_recovery': incremental,
            'active_cases': active_cases,
            'blocked_actions': blocked,
            'total_cases': total_cases,
            'recovered_cases': recovered_cases,
        }

    @staticmethod
    def get_recovery_funnel():
        total_failed = Payment.query.filter_by(status='failed').count()
        total_cases = RecoveryCase.query.count()
        actionable = RecoveryCase.query.filter(
            RecoveryCase.status.in_(['ACTION_PENDING', 'EXECUTING', 'RECOVERED', 'FAILED'])
        ).count()
        executed = RecoveryAction.query.filter(
            RecoveryAction.status.in_(['EXECUTED', 'SUCCESSFUL', 'FAILED'])
        ).count()
        recovered = RecoveryCase.query.filter_by(status='RECOVERED').count()

        return {
            'stages': [
                {'name': 'Failed Payments', 'count': total_failed},
                {'name': 'Recovery Cases', 'count': total_cases},
                {'name': 'Actionable', 'count': actionable},
                {'name': 'Actions Executed', 'count': executed},
                {'name': 'Recovered', 'count': recovered},
            ]
        }

    @staticmethod
    def get_failure_distribution():
        from app.utils.helpers import classify_failure
        payments = Payment.query.filter_by(status='failed').all()
        distribution = {}
        for p in payments:
            cat = classify_failure(p.failure_code, p.attempt_number)
            distribution[cat] = distribution.get(cat, 0) + 1
        return {
            'distribution': [
                {'category': k, 'count': v}
                for k, v in sorted(distribution.items(), key=lambda x: -x[1])
            ]
        }
