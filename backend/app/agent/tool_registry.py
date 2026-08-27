"""Tool registry for Gemini function calling."""

from typing import Dict, Any, List


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for Gemini's function calling."""
    return [
        {
            "name": "get_payment",
            "description": "Retrieve details of the failed payment",
            "input_schema": {
                "type": "object",
                "properties": {
                    "payment_id": {"type": "integer", "description": "Payment database ID"}
                },
                "required": ["payment_id"]
            }
        },
        {
            "name": "get_customer_history",
            "description": "Get customer transaction history and success rates",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": "Customer database ID"}
                },
                "required": ["customer_id"]
            }
        },
        {
            "name": "get_failure_context",
            "description": "Understand the failure pattern and category",
            "input_schema": {
                "type": "object",
                "properties": {
                    "failure_code": {"type": "string", "description": "Razorpay failure code"},
                    "payment_id": {"type": "integer", "description": "Payment database ID"}
                },
                "required": ["failure_code"]
            }
        },
        {
            "name": "predict_recovery",
            "description": "Get ML model prediction for recovery probability",
            "input_schema": {
                "type": "object",
                "properties": {
                    "payment_id": {"type": "integer", "description": "Payment database ID"}
                },
                "required": ["payment_id"]
            }
        },
        {
            "name": "get_policy",
            "description": "Retrieve merchant recovery policy configuration",
            "input_schema": {
                "type": "object",
                "properties": {
                    "merchant_id": {"type": "integer", "description": "Merchant database ID"}
                },
                "required": ["merchant_id"]
            }
        },
        {
            "name": "propose_recovery_action",
            "description": "Propose a recovery action (does not execute, just recommends)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": ["RETRY", "NOTIFY_CUSTOMER", "ALTERNATE_PAYMENT", "ESCALATE", "STOP"],
                        "description": "Type of recovery action"
                    },
                    "reason": {"type": "string", "description": "Why this action is recommended"},
                    "confidence": {"type": "number", "description": "Confidence 0-1"}
                },
                "required": ["action_type", "reason", "confidence"]
            }
        },
        {
            "name": "evaluate_policy",
            "description": "Check if an action is permitted by policy",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string", "description": "RETRY | NOTIFY_CUSTOMER | etc."},
                    "payment_id": {"type": "integer", "description": "Payment ID"}
                },
                "required": ["action_type", "payment_id"]
            }
        },
        {
            "name": "execute_retry",
            "description": "Execute a retry action (privileged—only after policy approval)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "recovery_case_id": {"type": "integer", "description": "Recovery case ID"},
                    "reason": {"type": "string", "description": "Reason for retry"}
                },
                "required": ["recovery_case_id", "reason"]
            }
        },
        {
            "name": "send_recovery_notification",
            "description": "Send customer notification about recovery options",
            "input_schema": {
                "type": "object",
                "properties": {
                    "recovery_case_id": {"type": "integer", "description": "Recovery case ID"},
                    "message": {"type": "string", "description": "Notification message"},
                    "channel": {"type": "string", "enum": ["email", "sms"], "description": "Notification channel"}
                },
                "required": ["recovery_case_id", "message", "channel"]
            }
        },
        {
            "name": "escalate_case",
            "description": "Mark case for human review and stop automated processing",
            "input_schema": {
                "type": "object",
                "properties": {
                    "recovery_case_id": {"type": "integer", "description": "Recovery case ID"},
                    "reason": {"type": "string", "description": "Reason for escalation"}
                },
                "required": ["recovery_case_id", "reason"]
            }
        }
    ]
