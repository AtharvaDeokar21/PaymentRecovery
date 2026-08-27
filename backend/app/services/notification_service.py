from app import db
from app.models.audit_log import AuditLog
from app.utils.helpers import utcnow
from app.utils.logging import get_logger

logger = get_logger('notification')


class NotificationService:
    @staticmethod
    def send_recovery_notification(customer, payment, recovery_case, channel='email'):
        """Simulate sending a recovery notification."""
        message = (
            f"Dear {customer.name}, your payment of ₹{payment.amount / 100:.2f} "
            f"could not be processed. Please try again or use an alternate payment method."
        )
        logger.info(f"[SIMULATED {channel.upper()}] To: {customer.email} - {message}")

        # Log the notification
        log = AuditLog(
            entity_type='recovery_case',
            entity_id=recovery_case.id,
            event_type='NOTIFICATION_SENT',
            actor='RecoverAI Agent',
            action=f'Recovery notification sent via {channel}',
            input_summary={'channel': channel, 'customer_email': customer.email},
            output_summary={'message': message, 'simulated': True},
        )
        db.session.add(log)
        db.session.commit()

        return {
            'status': 'sent',
            'channel': channel,
            'simulated': True,
            'message': message,
        }
