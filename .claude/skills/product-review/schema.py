"""Pydantic models for product-review Skill.

Interface contract — do NOT modify this file.
Colleague replaces reviewer.py internals only.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Enums (as Literal types for runtime validation)
# ---------------------------------------------------------------------------

Mode = Literal["evidence_review", "prd_review"]
Sufficiency = Literal["sufficient", "partial", "insufficient"]
Verdict = Literal["passed", "revision_required"]
FindingStatusEvidence = Literal["covered", "partial", "missing"]
FindingStatusPRD = Literal["ok", "issue", "critical"]
Severity = Literal["critical", "high", "medium", "low"]
Priority = Literal["high", "medium", "low"]
Strictness = Literal["standard", "strict"]

SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Helper models
# ---------------------------------------------------------------------------


class EvidenceFragment(BaseModel):
    """A single evidence fragment from upstream extraction."""

    content: str = Field(..., min_length=1, description="Evidence text content")
    source: str = Field(..., min_length=1, description="Source identifier")
    theme: Optional[str] = Field(None, description="Theme annotation (e.g., '疗效数据')")


class ReviewConfig(BaseModel):
    """Optional review configuration."""

    strictness: Strictness = Field("standard", description="Review strictness level")


class SupplementHint(BaseModel):
    """A supplement suggestion (evidence review mode only)."""

    information_type: str = Field(
        ..., min_length=1, description="Info type key (e.g., 'efficacy_data')"
    )
    priority: Priority = Field(..., description="Suggestion priority")
    description: str = Field(..., min_length=1, description="Direction for supplementing")


class RewriteTarget(BaseModel):
    """A rewrite target (PRD review mode only)."""

    section: str = Field(..., min_length=1, description="Target section name")
    severity: Severity = Field(..., description="Issue severity")
    issue: str = Field(..., min_length=1, description="Problem description")
    target: str = Field(..., min_length=1, description="Desired rewrite outcome")


class Finding(BaseModel):
    """A single review finding. Status enum varies by mode."""

    target_point: str = Field(..., min_length=1, description="Review focus point")
    status: str = Field(..., min_length=1, description="Status: covered|partial|missing (evidence) or ok|issue|critical (PRD)")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )
    detail: str = Field(..., min_length=1, description="Natural language explanation")
    suggestion: Optional[str] = Field(None, description="Improvement suggestion")


class ReviewError(BaseModel):
    """Structured error returned on input validation failure."""

    error: str = Field(..., description="Error code (e.g., 'empty_requirement')")
    message: str = Field(..., description="Human-readable error description")


# ---------------------------------------------------------------------------
# Core request / result
# ---------------------------------------------------------------------------


class ReviewRequest(BaseModel):
    """A review request. Mode determines which additional fields are required."""

    mode: Mode = Field(..., description="Review mode: evidence_review or prd_review")
    writing_requirement: str = Field(
        ...,
        min_length=1,
        description="Structured writing requirement in Markdown",
    )
    evidence_fragments: Optional[list[EvidenceFragment]] = Field(
        None, description="Evidence list (required for evidence_review)"
    )
    prd_content: Optional[str] = Field(
        None, description="PRD draft content (required for prd_review)"
    )
    config: Optional[ReviewConfig] = Field(None, description="Optional review config")

    @model_validator(mode="after")
    def validate_mode_fields(self) -> "ReviewRequest":
        if self.mode == "evidence_review":
            if self.evidence_fragments is None:
                raise ValueError(
                    "evidence_fragments is required when mode='evidence_review'"
                )
        elif self.mode == "prd_review":
            if not self.prd_content or not self.prd_content.strip():
                raise ValueError(
                    "prd_content is required and must be non-empty "
                    "when mode='prd_review'"
                )
        return self


class ReviewResult(BaseModel):
    """A complete review result. Mode-specific fields are None for the opposite mode."""

    mode: Mode = Field(..., description="Review mode (echo)")
    schema_version: str = Field(
        default=SCHEMA_VERSION, description="Schema version for compatibility"
    )
    findings: list[Finding] = Field(
        default_factory=list, description="Review finding list"
    )
    overall_assessment: str = Field(
        ..., min_length=1, description="Overall assessment in natural language"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-blocking warnings"
    )

    # Evidence review mode fields
    sufficiency: Optional[Sufficiency] = Field(
        None, description="Evidence sufficiency (evidence mode only)"
    )
    supplement_hints: Optional[list[SupplementHint]] = Field(
        None, description="Supplement suggestions (evidence mode only)"
    )
    ready_for_drafting: Optional[bool] = Field(
        None, description="Whether evidence is sufficient to proceed to drafting"
    )

    # PRD review mode fields
    verdict: Optional[Verdict] = Field(
        None, description="PRD review verdict (PRD mode only)"
    )
    rewrite_targets: Optional[list[RewriteTarget]] = Field(
        None, description="Rewrite targets (PRD mode only)"
    )
    ready_for_handoff: Optional[bool] = Field(
        None, description="Whether PRD can be handed off to writing Agent"
    )

    @model_validator(mode="after")
    def validate_mode_consistency(self) -> "ReviewResult":
        if self.mode == "evidence_review":
            if self.verdict is not None:
                raise ValueError("verdict must be None for evidence_review mode")
            if self.rewrite_targets is not None:
                raise ValueError("rewrite_targets must be None for evidence_review mode")
            if self.ready_for_handoff is not None:
                raise ValueError("ready_for_handoff must be None for evidence_review mode")
        elif self.mode == "prd_review":
            if self.sufficiency is not None:
                raise ValueError("sufficiency must be None for prd_review mode")
            if self.supplement_hints is not None:
                raise ValueError("supplement_hints must be None for prd_review mode")
            if self.ready_for_drafting is not None:
                raise ValueError("ready_for_drafting must be None for prd_review mode")
        return self
