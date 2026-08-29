export interface Payment {
  id: number;
  merchant_id: number;
  customer_id: number;
  razorpay_order_id: string;
  razorpay_payment_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  failure_code: string;
  failure_reason: string;
  attempt_number: number;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: number;
  merchant_id: number;
  external_customer_id: string;
  name: string;
  email: string;
  phone: string;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  lifetime_value: number;
  success_rate: number;
  created_at: string;
}

export interface RecoveryCase {
  id: number;
  payment_id: number;
  status: string;
  recovery_probability: number | null;
  revenue_at_risk: number;
  expected_recovery: number | null;
  diagnosis: string | null;
  recommended_action: string | null;
  confidence: number | null;
  priority: string;
  created_at: string;
  updated_at: string;
  payment?: Payment;
  customer?: Customer;
}

export interface DashboardSummary {
  revenue_at_risk: number;
  recovered_revenue: number;
  recovery_rate: number;
  incremental_recovery: number;
  active_cases: number;
  blocked_actions: number;
  total_cases: number;
  recovered_cases: number;
}

export interface AuditLog {
  id: number;
  entity_type: string;
  entity_id: number;
  event_type: string;
  actor: string;
  action: string;
  input_summary: any;
  output_summary: any;
  policy_result: any;
  timestamp: string;
}

export interface Policy {
  id?: number;
  merchant_id: number;
  max_retry_attempts: number;
  max_auto_retry_amount: number;
  min_recovery_probability: number;
  approval_threshold: number;
  cooldown_minutes: number;
  created_at?: string;
  updated_at?: string;
}
