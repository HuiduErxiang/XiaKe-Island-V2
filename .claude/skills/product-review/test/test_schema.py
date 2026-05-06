"""Schema validation tests (US3).

Validates Pydantic models for all entities, enum constraints, and mode-dependent validators.
Covers SC-002: Schema validation 100%.
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from schema import (
    EvidenceFragment,
    Finding,
    ReviewConfig,
    ReviewRequest,
    ReviewResult,
    SupplementHint,
    RewriteTarget,
    ReviewError,
)


class TestEvidenceFragment:
    def test_valid_fragment(self):
        ef = EvidenceFragment(content="test content", source="source1")
        assert ef.content == "test content"
        assert ef.source == "source1"
        assert ef.theme is None

    def test_valid_fragment_with_theme(self):
        ef = EvidenceFragment(content="test", source="s1", theme="疗效数据")
        assert ef.theme == "疗效数据"

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            EvidenceFragment(content="", source="s1")

    def test_empty_source_rejected(self):
        with pytest.raises(ValidationError):
            EvidenceFragment(content="test", source="")


class TestReviewRequest:
    def test_evidence_mode_valid(self):
        req = ReviewRequest(
            mode="evidence_review",
            writing_requirement="## 需求\n测试",
            evidence_fragments=[{"content": "c", "source": "s"}],
        )
        assert req.mode == "evidence_review"

    def test_prd_mode_valid(self):
        req = ReviewRequest(
            mode="prd_review",
            writing_requirement="## 需求\n测试",
            prd_content="## PRD\n内容",
        )
        assert req.mode == "prd_review"

    def test_evidence_mode_missing_fragments(self):
        with pytest.raises(ValidationError):
            ReviewRequest(
                mode="evidence_review",
                writing_requirement="## test",
            )

    def test_prd_mode_missing_content(self):
        with pytest.raises(ValidationError):
            ReviewRequest(
                mode="prd_review",
                writing_requirement="## test",
            )

    def test_empty_writing_requirement(self):
        with pytest.raises(ValidationError):
            ReviewRequest(
                mode="evidence_review",
                writing_requirement="",
                evidence_fragments=[{"content": "c", "source": "s"}],
            )


class TestReviewResult:
    def test_evidence_result(self):
        result = ReviewResult(
            mode="evidence_review",
            sufficiency="sufficient",
            ready_for_drafting=True,
            supplement_hints=[
                SupplementHint(
                    information_type="efficacy_data",
                    priority="high",
                    description="test",
                )
            ],
            findings=[Finding(target_point="test", status="covered", confidence=0.9, detail="ok")],
            overall_assessment="All good",
        )
        assert result.sufficiency == "sufficient"
        assert result.verdict is None

    def test_prd_result(self):
        result = ReviewResult(
            mode="prd_review",
            verdict="passed",
            ready_for_handoff=True,
            findings=[Finding(target_point="test", status="ok", confidence=0.9, detail="ok")],
            overall_assessment="All good",
        )
        assert result.verdict == "passed"
        assert result.sufficiency is None

    def test_mode_inconsistency_rejected(self):
        with pytest.raises(ValidationError):
            ReviewResult(
                mode="evidence_review",
                verdict="passed",  # wrong mode field
                findings=[],
                overall_assessment="test",
            )

    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            Finding(target_point="x", status="covered", confidence=1.5, detail="x")


class TestReviewError:
    def test_error_structure(self):
        err = ReviewError(error="empty_requirement", message="不能为空")
        assert err.error == "empty_requirement"
        assert err.message == "不能为空"
