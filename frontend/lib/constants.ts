export const FAILURE_CATEGORIES = {
  TRANSIENT: { label: 'Transient', color: 'bg-blue-500' },
  CUSTOMER_FUNDS: { label: 'Insufficient Funds', color: 'bg-orange-500' },
  PAYMENT_METHOD: { label: 'Payment Method', color: 'bg-purple-500' },
  ISSUER_DECLINE: { label: 'Issuer Decline', color: 'bg-red-500' },
  REPEATED_FAILURE: { label: 'Repeated Failure', color: 'bg-gray-500' },
  UNKNOWN: { label: 'Unknown', color: 'bg-slate-500' },
};

export const RECOVERY_STATUS_COLORS = {
  DETECTED: 'bg-slate-100 text-slate-700',
  ANALYZING: 'bg-blue-100 text-blue-700',
  ACTION_PENDING: 'bg-yellow-100 text-yellow-700',
  EXECUTING: 'bg-indigo-100 text-indigo-700',
  RECOVERED: 'bg-green-100 text-green-700',
  FAILED: 'bg-red-100 text-red-700',
  ESCALATED: 'bg-orange-100 text-orange-700',
  BLOCKED: 'bg-gray-100 text-gray-700',
  CLOSED: 'bg-slate-100 text-slate-500',
};

export const ACTION_TYPES = {
  RETRY: 'Retry Payment',
  NOTIFY_CUSTOMER: 'Notify Customer',
  ALTERNATE_PAYMENT: 'Alternate Payment Method',
  ESCALATE: 'Escalate',
  STOP: 'Stop',
};
