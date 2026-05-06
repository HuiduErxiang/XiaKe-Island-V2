"""Determinism tests (US3).

Verifies SC-003: Same input called 10 times produces 100% identical output.
Covered for both evidence_review and prd_review modes.
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


class TestDeterminism:
    def test_evidence_review_deterministic(self):
        """10 identical evidence review calls produce identical output."""
        fx = _load_fixture("evidence_review", "partial_evidence.json")
        results = []
        for _ in range(10):
            result = review(
                mode="evidence_review",
                writing_requirement=fx["writing_requirement"],
                evidence_fragments=fx["evidence_fragments"],
            )
            results.append(json.dumps(result, sort_keys=True, ensure_ascii=False))

        first = results[0]
        for i, r in enumerate(results[1:], start=2):
            assert r == first, f"Call #{i} produced different output"

    def test_prd_review_deterministic(self):
        """10 identical PRD review calls produce identical output."""
        fx = _load_fixture("prd_review", "revision_prd.json")
        results = []
        for _ in range(10):
            result = review(
                mode="prd_review",
                writing_requirement=fx["writing_requirement"],
                prd_content=fx["prd_content"],
            )
            results.append(json.dumps(result, sort_keys=True, ensure_ascii=False))

        first = results[0]
        for i, r in enumerate(results[1:], start=2):
            assert r == first, f"Call #{i} produced different output"

    def test_error_responses_deterministic(self):
        """Error responses are also deterministic."""
        results = []
        for _ in range(10):
            result = review(
                mode="evidence_review",
                writing_requirement="",
                evidence_fragments=[],
            )
            results.append(json.dumps(result, sort_keys=True))

        first = results[0]
        for i, r in enumerate(results[1:], start=2):
            assert r == first, f"Call #{i} produced different error output"
