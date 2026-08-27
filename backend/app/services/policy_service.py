from app import db
from app.models.policy import Policy
from app.services.audit_service import AuditService


class PolicyService:
    @staticmethod
    def get_policies(merchant_id=1):
        policy = Policy.query.filter_by(merchant_id=merchant_id).first()
        if not policy:
            return {
                'merchant_id': merchant_id,
                'max_retry_attempts': 2,
                'max_auto_retry_amount': 1000000,
                'min_recovery_probability': 0.65,
                'approval_threshold': 1000000,
                'cooldown_minutes': 15,
            }
        return policy.to_dict()

    @staticmethod
    def update_policies(merchant_id, data):
        policy = Policy.query.filter_by(merchant_id=merchant_id).first()
        if not policy:
            policy = Policy(merchant_id=merchant_id)
            db.session.add(policy)

        allowed_fields = [
            'max_retry_attempts', 'max_auto_retry_amount',
            'min_recovery_probability', 'approval_threshold', 'cooldown_minutes'
        ]
        old_values = {}
        new_values = {}
        for field in allowed_fields:
            if field in data:
                old_values[field] = getattr(policy, field)
                setattr(policy, field, data[field])
                new_values[field] = data[field]

        db.session.commit()

        AuditService.log(
            entity_type='policy',
            entity_id=policy.id,
            event_type='POLICY_UPDATED',
            actor='Merchant',
            action='Policy configuration updated',
            input_summary=old_values,
            output_summary=new_values,
        )

        return policy.to_dict()
