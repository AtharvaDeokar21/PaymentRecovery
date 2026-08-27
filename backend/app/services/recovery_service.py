from app import db
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.payment import Payment
from app.models.agent_decision import AgentDecision
from app.models.audit_log import AuditLog
from app.utils.helpers import utcnow


class RecoveryService:
    @staticmethod
    def list_cases(status=None, page=1, per_page=20):
        query = RecoveryCase.query
        if status:
            query = query.filter(RecoveryCase.status == status)
        query = query.order_by(RecoveryCase.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        cases = []
        for case in pagination.items:
            d = case.to_dict()
            d['payment'] = case.payment.to_dict() if case.payment else None
            if case.payment and case.payment.customer:
                d['customer'] = case.payment.customer.to_dict()
            cases.append(d)
        return {
            'cases': cases,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        }

    @staticmethod
    def get_case_detail(case_id):
        case = RecoveryCase.query.get(case_id)
        if not case:
            return None
        result = case.to_dict()
        result['payment'] = case.payment.to_dict() if case.payment else None
        if case.payment and case.payment.customer:
            result['customer'] = case.payment.customer.to_dict()
        result['actions'] = [a.to_dict() for a in case.actions.order_by(RecoveryAction.id.asc())]
        result['decisions'] = [d.to_dict() for d in case.decisions.order_by(AgentDecision.created_at.desc())]
        result['audit_trail'] = [
            l.to_dict() for l in AuditLog.query.filter_by(
                entity_type='recovery_case', entity_id=case_id
            ).order_by(AuditLog.timestamp.asc()).all()
        ]
        return result

    @staticmethod
    def analyze_case(case_id):
        case = RecoveryCase.query.get(case_id)
        if not case:
            return {'error': 'Case not found'}
        # Delegate to agent — will be implemented in Phase 6
        from app.agent.recovery_agent import RecoveryAgent
        agent = RecoveryAgent()
        result = agent.analyze(case_id)
        return result

    @staticmethod
    def execute_recovery(case_id):
        case = RecoveryCase.query.get(case_id)
        if not case:
            return {'error': 'Case not found'}
        from app.agent.recovery_agent import RecoveryAgent
        agent = RecoveryAgent()
        result = agent.execute(case_id)
        return result

    @staticmethod
    def escalate_case(case_id):
        case = RecoveryCase.query.get(case_id)
        if not case:
            return {'error': 'Case not found'}
        case.status = 'ESCALATED'
        db.session.add(AuditLog(
            entity_type='recovery_case',
            entity_id=case_id,
            event_type='ESCALATED',
            actor='Merchant',
            action='Manual escalation',
        ))
        db.session.commit()
        return case.to_dict()
