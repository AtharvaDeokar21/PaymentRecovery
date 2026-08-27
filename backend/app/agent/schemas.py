"""Pydantic schemas for agent responses and tool calls."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class AgentDiagnosis(BaseModel):
    """Agent diagnosis of payment failure."""
    failure_category: str = Field(..., description="TRANSIENT | CUSTOMER_FUNDS | PAYMENT_METHOD | ISSUER_DECLINE | REPEATED_FAILURE | UNKNOWN")
    root_cause: str = Field(..., description="Why did the payment fail?")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this diagnosis (0-1)")


class AgentRecommendation(BaseModel):
    """Agent recommendation for recovery action."""
    action: str = Field(..., description="RETRY | NOTIFY_CUSTOMER | ALTERNATE_PAYMENT | ESCALATE | STOP")
    reasoning: str = Field(..., description="Why is this action recommended?")
    evidence: List[str] = Field(default_factory=list, description="Evidence supporting the recommendation")
    recovery_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated recovery probability")


class AgentDecisionResponse(BaseModel):
    """Complete agent decision response."""
    diagnosis: AgentDiagnosis
    recommendation: AgentRecommendation
    confidence_overall: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in recommendation")
    reasoning_summary: str = Field(..., description="Brief summary of the reasoning process")
