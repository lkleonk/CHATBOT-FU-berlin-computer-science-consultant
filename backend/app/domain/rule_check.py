from typing import Any, Literal

from pydantic import BaseModel, Field


class RuleIssue(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class RuleCheckResult(BaseModel):
    is_valid: bool
    summary: str
    totals: dict[str, int] = Field(default_factory=dict)
    issues: list[RuleIssue] = Field(default_factory=list)
