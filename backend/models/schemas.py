"""
Pydantic models for request/response validation.
Covers all endpoints in the 16-step pipeline.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ── Request Models ─────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None
    history: list[dict] = Field(default_factory=list)


class BlueprintUpdateRequest(BaseModel):
    blueprint_id: str
    nodes: list[dict]
    edges: list[dict]


class NativeMappingRequest(BaseModel):
    blueprint_id: str
    provider: str  # "aws", "gcp", "azure"
    region: str = "us-east-1"


class RefinementRequest(BaseModel):
    """For iterative refinement — user tweaks constraints and re-runs scoring."""
    chat_id: str
    blueprint_id: str
    updated_constraints: dict = Field(default_factory=dict)


# ── Response Models ────────────────────────────────────────

class ConstraintField(BaseModel):
    value: Optional[Any] = None
    status: str = "MISSING"  # KNOWN | INFERRED | MISSING


class IntentAnalysis(BaseModel):
    intent: str = "web_app"
    stage: str = "production"
    constraints: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    missing_critical: list[str] = Field(default_factory=list)
    follow_up_question: Optional[str] = None


class BlueprintNode(BaseModel):
    id: str
    type: str
    category: str = "compute"
    x: float = 0
    y: float = 0
    label: str = ""


class BlueprintEdge(BaseModel):
    source: str
    target: str


class ProviderScore(BaseModel):
    id: str
    name: str
    totalScore: int = 0
    dimensions: dict[str, int] = Field(default_factory=dict)
    reasoning: str = ""


class DeploymentPlan(BaseModel):
    expected_latency_ms: Optional[int] = None
    concurrency_limit: Optional[int] = None
    total_users_capacity: Optional[int] = None
    compliance_status: list[str] = Field(default_factory=list)
    scalability_rating: str = "Unknown"


class ChatResponse(BaseModel):
    chat_id: str
    phase: str  # "clarifying" | "scored" | "error"
    explanation: str = ""
    follow_up_question: Optional[str] = None
    blueprint: Optional[dict] = None
    scoring: Optional[list[dict]] = None
    intent_analysis: Optional[dict] = None
    theory_context: Optional[str] = None
    deployment_plan: Optional[DeploymentPlan] = None


class BlueprintResponse(BaseModel):
    blueprint_id: str
    type: str = "generic"
    provider: str = "generic"
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    scores: Optional[dict] = None
    explanation: str = ""
    native_mapping: Optional[dict] = None
    created_at: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    chat_id: str
    messages: list[dict] = Field(default_factory=list)
    summary: str = ""
    metadata: dict = Field(default_factory=dict)


class ChatSessionSummary(BaseModel):
    chat_id: str
    intent: str = "web_app"
    summary: str = ""
    updated_at: Optional[str] = None


class ListChatsResponse(BaseModel):
    chats: list[ChatSessionSummary] = Field(default_factory=list)


class NativeMappingResponse(BaseModel):
    native_blueprint_id: str
    provider: str
    mapping: dict = Field(default_factory=dict)
    total_estimated_cost: Optional[float] = None


# ── Market Intelligence Models ────────────────────────────

class PerformanceMetrics(BaseModel):
    latency_ms: Optional[int] = None
    throughput: Optional[str] = None
    concurrent_users_limit: Optional[int] = None
    scalability: str = "Unknown"


class ComplianceInfo(BaseModel):
    certifications: list[str] = Field(default_factory=list)
    regions_supported: list[str] = Field(default_factory=list)


class ServiceIntel(BaseModel):
    provider: str
    service: str
    free_tier_details: str
    usage_limits: dict = Field(default_factory=dict)
    performance: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    compliance: ComplianceInfo = Field(default_factory=ComplianceInfo)
    paid_offerings_summary: str = ""
    last_updated: datetime = Field(default_factory=datetime.utcnow)
