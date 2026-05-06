"""Entry point for product-review Skill.

Validates input, dispatches to reviewer, and assembles output.
Do NOT modify this file — it is part of the interface contract.
"""

from __future__ import annotations

from schema import SCHEMA_VERSION, EvidenceFragment, ReviewRequest, ReviewResult
from reviewer import evidence_review, prd_review

VALID_MODES = {"evidence_review", "prd_review"}


def _validate_fragments(
    raw_fragments: list[dict],
) -> tuple[list[dict], list[str]]:
    """Validate evidence fragments individually, skipping malformed entries."""
    valid = []
    warnings = []
    for i, frag in enumerate(raw_fragments):
        if not isinstance(frag, dict):
            warnings.append(f"证据片段 #{i} 格式无效，已跳过")
            continue
        try:
            ef = EvidenceFragment(**frag)
            valid.append(ef.model_dump())
        except Exception:
            warnings.append(f"证据片段 #{i} 缺少必要字段或内容为空，已跳过")
    return valid, warnings


def review(
    mode: str,
    writing_requirement: str,
    evidence_fragments: list[dict] | None = None,
    prd_content: str | None = None,
    config: dict | None = None,
) -> dict:
    """Public entry point for product review.

    Returns ReviewResult as a dict on success, or ReviewError dict on input failure.
    """

    # -- Input validation --
    if not writing_requirement or not writing_requirement.strip():
        return {"error": "empty_requirement", "message": "写作需求不能为空"}

    if mode not in VALID_MODES:
        return {
            "error": "invalid_mode",
            "message": f"无效的审核模式 '{mode}'，支持 evidence_review 或 prd_review",
        }

    warnings: list[str] = []

    if mode == "evidence_review":
        if evidence_fragments is None:
            return {
                "error": "missing_evidence",
                "message": "证据审核模式下 evidence_fragments 为必填参数",
            }
        # Validate fragments individually, skip malformed ones
        evidence_fragments, frag_warnings = _validate_fragments(evidence_fragments)
        warnings.extend(frag_warnings)
    elif mode == "prd_review":
        if not prd_content or not prd_content.strip():
            return {
                "error": "missing_prd",
                "message": "PRD 审核模式下 prd_content 为必填参数且不能为空",
            }

    # -- Build and validate request (Pydantic schema check) --
    try:
        request = ReviewRequest(
            mode=mode,
            writing_requirement=writing_requirement.strip(),
            evidence_fragments=evidence_fragments,
            prd_content=prd_content,
            config=config,
        )
    except ValueError as exc:
        return {
            "error": "validation_error",
            "message": str(exc),
        }

    # -- Dispatch to reviewer --
    if mode == "evidence_review":
        result_data = evidence_review(
            writing_requirement=request.writing_requirement,
            evidence_fragments=request.evidence_fragments or [],
        )
    else:
        result_data = prd_review(
            writing_requirement=request.writing_requirement,
            prd_content=request.prd_content or "",
        )

    # Merge fragment warnings
    if warnings:
        result_data["warnings"] = warnings + result_data.get("warnings", [])

    # -- Assemble and validate result (Pydantic schema check) --
    result = ReviewResult(
        mode=mode,
        schema_version=SCHEMA_VERSION,
        findings=result_data.get("findings", []),
        overall_assessment=result_data.get("overall_assessment", ""),
        warnings=result_data.get("warnings", []),
        sufficiency=result_data.get("sufficiency"),
        supplement_hints=result_data.get("supplement_hints"),
        ready_for_drafting=result_data.get("ready_for_drafting"),
        verdict=result_data.get("verdict"),
        rewrite_targets=result_data.get("rewrite_targets"),
        ready_for_handoff=result_data.get("ready_for_handoff"),
    )

    return result.model_dump()
