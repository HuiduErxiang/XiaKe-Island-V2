"""Unit tests for PRD review mode (US2).

Covers spec acceptance scenarios:
  1. Well-structured PRD → verdict=passed, ready_for_handoff=true
  2. PRD with logic gaps → verdict=revision_required
  3. PRD with compliance issues → finding severity=critical
  4. Empty/minimal PRD → verdict=revision_required, no crash
"""

import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from main import review  # noqa: E402


def _load_fixture(name: str) -> dict:
    path = SKILL_DIR / "test" / "fixtures" / "prd_review" / name
    with open(path) as f:
        return json.load(f)


class TestPRDReview:
    def test_passed_prd(self):
        """US2 Scenario 1: 结构完整、论证有据的 PRD 返回 passed"""
        fx = _load_fixture("passed_prd.json")
        result = review(
            mode="prd_review",
            writing_requirement=fx["writing_requirement"],
            prd_content=fx["prd_content"],
        )
        assert result["verdict"] == "passed"
        assert result["ready_for_handoff"] is True
        assert len(result["findings"]) > 0
        assert result["mode"] == "prd_review"
        assert result["schema_version"] == "1.0"
        assert isinstance(result["overall_assessment"], str)

    def test_revision_required_prd(self):
        """US2 Scenario 2: 缺乏论证的 PRD 返回 revision_required"""
        fx = _load_fixture("revision_prd.json")
        result = review(
            mode="prd_review",
            writing_requirement=fx["writing_requirement"],
            prd_content=fx["prd_content"],
        )
        assert result["verdict"] == "revision_required"
        assert result["ready_for_handoff"] is False
        # Should have rewrite targets
        assert result["rewrite_targets"] is not None

    def test_prd_with_compliance_issue(self):
        """US2 Scenario 3: 含合规红线的 PRD，finding severity=critical"""
        result = review(
            mode="prd_review",
            writing_requirement="## 写作需求\n写一篇关于新药的科普文章。\n\n- 疗效数据\n- 安全性数据",
            prd_content="## 疗效分析\n\n这是神药，可以根治阿尔茨海默病，100%有效，绝对安全无任何副作用。",
        )
        assert result["verdict"] == "revision_required"
        assert result["ready_for_handoff"] is False
        critical_findings = [
            f for f in result["findings"] if f["status"] == "critical"
        ]
        assert len(critical_findings) > 0

    def test_empty_prd(self):
        """US2 Scenario 4: 空 PRD 不崩溃，返回 revision_required"""
        result = review(
            mode="prd_review",
            writing_requirement="## 写作需求\n写一篇科普文章。",
            prd_content="## 标题\n",
        )
        assert result["verdict"] == "revision_required"
        assert len(result["findings"]) > 0
