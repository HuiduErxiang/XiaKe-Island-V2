"""Unit tests for evidence review mode (US1).

Covers spec acceptance scenarios:
  1. Partial evidence → sufficiency=partial
  2. Sufficient evidence → sufficiency=sufficient, ready_for_drafting=true
  3. Insufficient evidence → sufficiency=insufficient
  4. Empty evidence → sufficiency=insufficient, no crash
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure the skill package is importable
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from main import review  # noqa: E402


def _load_fixture(name: str) -> dict:
    path = SKILL_DIR / "test" / "fixtures" / "evidence_review" / name
    with open(path) as f:
        return json.load(f)


class TestEvidenceReview:
    def test_partial_evidence(self):
        """US1 Scenario 1: 证据部分覆盖时返回 partial"""
        fx = _load_fixture("partial_evidence.json")
        result = review(
            mode="evidence_review",
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=fx["evidence_fragments"],
        )
        assert result["sufficiency"] == "partial"
        assert result["ready_for_drafting"] is False
        assert len(result["findings"]) > 0
        assert result["supplement_hints"] is not None
        assert len(result["supplement_hints"]) > 0
        # All required fields present
        assert result["mode"] == "evidence_review"
        assert result["schema_version"] == "1.0"
        assert isinstance(result["overall_assessment"], str)
        assert len(result["overall_assessment"]) > 0

    def test_sufficient_evidence(self):
        """US1 Scenario 2: 证据全部覆盖时返回 sufficient"""
        fx = _load_fixture("sufficient_evidence.json")
        result = review(
            mode="evidence_review",
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=fx["evidence_fragments"],
        )
        assert result["sufficiency"] == "sufficient"
        assert result["ready_for_drafting"] is True

    def test_insufficient_evidence(self):
        """US1 Scenario 3: 证据严重不足时返回 insufficient"""
        fx = _load_fixture("insufficient_evidence.json")
        result = review(
            mode="evidence_review",
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=fx["evidence_fragments"],
        )
        assert result["sufficiency"] == "insufficient"
        assert result["ready_for_drafting"] is False
        assert result["supplement_hints"] is not None
        # supplement_hints should mention missing info types
        hints = result["supplement_hints"]
        info_types = [h["information_type"] for h in hints]
        assert any("安全" in t or "safety" in t for t in info_types)

    def test_empty_evidence_list(self):
        """US1 Scenario 4: 空证据列表不崩溃，返回 insufficient"""
        fx = _load_fixture("insufficient_evidence.json")
        result = review(
            mode="evidence_review",
            writing_requirement=fx["writing_requirement"],
            evidence_fragments=[],
        )
        assert result["sufficiency"] == "insufficient"
        assert len(result["findings"]) > 0
        # All info points should be missing
        for f_item in result["findings"]:
            assert f_item["status"] == "missing"
