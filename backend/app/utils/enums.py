from enum import Enum


class PaymentStatus(str, Enum):
    CREATED = 'created'
    AUTHORIZED = 'authorized'
    CAPTURED = 'captured'
    FAILED = 'failed'
    REFUNDED = 'refunded'


class FailureCategory(str, Enum):
    TRANSIENT = 'TRANSIENT'
    CUSTOMER_FUNDS = 'CUSTOMER_FUNDS'
    PAYMENT_METHOD = 'PAYMENT_METHOD'
    ISSUER_DECLINE = 'ISSUER_DECLINE'
    REPEATED_FAILURE = 'REPEATED_FAILURE'
    UNKNOWN = 'UNKNOWN'


class RecoveryCaseStatus(str, Enum):
    DETECTED = 'DETECTED'
    ANALYZING = 'ANALYZING'
    ACTION_PENDING = 'ACTION_PENDING'
    EXECUTING = 'EXECUTING'
    RECOVERED = 'RECOVERED'
    FAILED = 'FAILED'
    ESCALATED = 'ESCALATED'
    BLOCKED = 'BLOCKED'
    CLOSED = 'CLOSED'


class ActionType(str, Enum):
    RETRY = 'RETRY'
    NOTIFY_CUSTOMER = 'NOTIFY_CUSTOMER'
    ALTERNATE_PAYMENT = 'ALTERNATE_PAYMENT'
    ESCALATE = 'ESCALATE'
    STOP = 'STOP'


class ActionStatus(str, Enum):
    RECOMMENDED = 'RECOMMENDED'
    AUTHORIZED = 'AUTHORIZED'
    EXECUTED = 'EXECUTED'
    SUCCESSFUL = 'SUCCESSFUL'
    FAILED = 'FAILED'
    BLOCKED = 'BLOCKED'


class Priority(str, Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'
