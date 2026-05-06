"""Integration tests (US3).

Full review() call chain for both modes, error response paths, and edge cases.
"""

import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from main import review  # noqa: E402


def _load_fixture(subdir: str, name: str) -> dict:
    path = SKILL_DIR / "test" / "fixtures" / subdir / name
    with open(path) as f:
        return json.load(f)


class TestIntegration:
    # -- Evidence mode full chain --

    def test_evidence_full_chain_sufficient(self):
        fx = _load_fixture("evidence_review", "sufficient_evidence.json")
        result = review(
            mode=fx["mode"],
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=fx["evidence_fragments"],
        )
        assert result["sufficiency"] == fx["expected"]["sufficiency"]
        assert result["ready_for_drafting"] == fx["expected"]["ready_for_drafting"]
        assert result["mode"] == "evidence_review"
        assert result["schema_version"] == "1.0"
        assert result["verdict"] is None
        assert result["rewrite_targets"] is None
        assert result["ready_for_handoff"] is None

    def test_evidence_full_chain_insufficient(self):
        fx = _load_fixture("evidence_review", "insufficient_evidence.json")
        result = review(
            mode=fx["mode"],
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=fx["evidence_fragments"],
        )
        assert result["sufficiency"] == "insufficient"
        assert result["ready_for_drafting"] is False
        assert len(result["supplement_hints"]) > 0
        # supplement_hints capped at max 5
        assert len(result["supplement_hints"]) <= 5

    # -- PRD mode full chain --

    def test_prd_full_chain_passed(self):
        fx = _load_fixture("prd_review", "passed_prd.json")
        result = review(
            mode=fx["mode"],
            writing_requirement=fx["writing_requirement"],
            prd_content=fx["prd_content"],
        )
        assert result["verdict"] == "passed"
        assert result["ready_for_handoff"] is True
        assert result["sufficiency"] is None
        assert result["supplement_hints"] is None
        assert result["ready_for_drafting"] is None

    def test_prd_full_chain_revision(self):
        fx = _load_fixture("prd_review", "revision_prd.json")
        result = review(
            mode=fx["mode"],
            writing_requirement=fx["writing_requirement"],
            prd_content=fx["prd_content"],
        )
        assert result["verdict"] == "revision_required"
        assert result["ready_for_handoff"] is False
        assert len(result["rewrite_targets"]) > 0

    # -- Error paths --

    def test_empty_requirement_error(self):
        fx = _load_fixture("edge_cases", "empty_requirement.json")
        result = review(
            mode=fx["mode"],
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=fx["evidence_fragments"],
        )
        assert "error" in result
        assert result["error"] == "empty_requirement"

    def test_invalid_mode_error(self):
        fx = _load_fixture("edge_cases", "invalid_mode.json")
        result = review(
            mode=fx["mode"],
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=fx["evidence_fragments"],
        )
        assert "error" in result
        assert result["error"] == "invalid_mode"

    def test_missing_evidence_error(self):
        result = review(
            mode="evidence_review",
            writing_requirement="## test",
        )
        assert result["error"] == "missing_evidence"

    def test_missing_prd_error(self):
        result = review(
            mode="prd_review",
            writing_requirement="## test",
        )
        assert result["error"] == "missing_prd"

    # -- Edge case: PRD truncated review --

    def test_prd_truncated_review(self):
        fx = _load_fixture("edge_cases", "truncated_prd.json")
        result = review(
            mode=fx["mode"],
            writing_requirement=fx["writing_requirement"],
            prd_content=fx["prd_content"],
        )
        assert "warnings" in result
        assert any("truncated" in w.lower() or "50000" in w for w in result["warnings"])

    # -- Edge case: CN requirement + EN evidence --

    def test_language_mismatch(self):
        fx = _load_fixture("edge_cases", "language_mismatch.json")
        result = review(
            mode=fx["mode"],
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=fx["evidence_fragments"],
        )
        # Should not crash, returns a valid result
        assert "sufficiency" in result
        assert result["sufficiency"] in ("sufficient", "partial", "insufficient")

    # -- Malformed evidence --

    def test_malformed_evidence(self):
        result = review(
            mode="evidence_review",
            writing_requirement="## 写作需求\n测试疗效数据",
            evidence_fragments=[
                {"content": "valid", "source": "s1"},
                {"content": "", "source": "s2"},  # empty content
                {"source": "missing_content"},  # missing content field
            ],
        )
        # Should skip malformed entries and warn, not crash
        assert "warnings" in result
        assert len(result["warnings"]) >= 2
        assert "sufficiency" in result
