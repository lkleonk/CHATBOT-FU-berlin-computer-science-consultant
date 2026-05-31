from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.study_plan import StudyPlan


class MessageRequest(BaseModel):
    content: str = Field(min_length=1)


class SessionResponse(BaseModel):
    session_id: str


class Citation(BaseModel):
    source: str
    title: str | None = None
    section_heading: str | None = None
    page: int | None = None
    score: float | None = None


class RuleIssue(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class RuleCheckResponse(BaseModel):
    is_valid: bool
    summary: str
    totals: dict[str, int] = Field(default_factory=dict)
    issues: list[RuleIssue] = Field(default_factory=list)


class ModelReply(BaseModel):
    reply: str
    message_type: Literal["study_question", "plan_check", "off_topic"]
    citations: list[Citation] = Field(default_factory=list)
    rule_check_result: RuleCheckResponse | None = None
    parsed_study_plan: StudyPlan | None = None


class TranscriptUploadResponse(BaseModel):
    filename: str
    message_type: Literal["plan_check"] = "plan_check"
    reply: str
    parsed_study_plan: StudyPlan | None = None
    rule_check_result: RuleCheckResponse | None = None


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    services: dict[str, str]
