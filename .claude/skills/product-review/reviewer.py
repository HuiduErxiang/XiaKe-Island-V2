"""Review logic — mock implementation using rule-based keyword matching.

This file is designed to be REPLACED by colleague with real review logic
(e.g., LLM-based, cang rule-engine, etc.). The public function signatures
must be preserved to maintain compatibility with main.py.
"""

from __future__ import annotations

from schema import (
    Finding,
    Priority,
    RewriteTarget,
    Severity,
    Sufficiency,
    SupplementHint,
    Verdict,
)

# ---------------------------------------------------------------------------
# Information point types (8 categories) — evidence review
# ---------------------------------------------------------------------------

INFO_POINTS: dict[str, list[str]] = {
    "疗效数据": ["疗效", "有效率", "ORR", "PFS", "OS", "缓解率", "临床终点", "CDR-SB", "MMSE"],
    "安全性数据": ["安全性", "不良反应", "不良事件", "AE", "SAE", "耐受性", "ARIA"],
    "作用机制": ["机制", "MOA", "靶点", "通路", "药理", "原纤维", "Aβ", "淀粉样蛋白"],
    "经济性评估": ["经济性", "成本效益", "ICER", "QALY", "药物经济学", "成本"],
    "流行病学数据": ["流行病学", "发病率", "患病率", "流行病学"],
    "用法用量": ["用法", "用量", "剂量", "给药方案", "给药方式", "mg"],
    "临床指南引用": ["指南", "推荐", "CSCO", "NCCN", "共识", "推荐意见"],
    "头对头研究": ["头对头", "对比研究", "对照试验", "vs", "相较于"],
}

# ---------------------------------------------------------------------------
# PRD defect patterns (4 categories) — PRD review
# ---------------------------------------------------------------------------

DEFECT_PATTERNS: dict[str, dict] = {
    "论证无据": {
        "severity": "high",
        "keywords": ["。", "因此", "所以", "可见", "这表明"],
        "check": "claim_without_citation",
    },
    "逻辑跳跃": {
        "severity": "medium",
        "keywords": ["首先", "其次", "然后", "接下来", "此外", "一方面"],
        "check": "transition_missing",
    },
    "结构缺失": {
        "severity": "high",
        "expected_sections": ["疗效", "安全性", "作用机制", "经济性", "流行病学", "用法用量"],
        "check": "section_missing",
    },
    "合规红线": {
        "severity": "critical",
        "keywords": ["治愈", "根治", "神药", "万能", "无任何副作用", "100%有效", "绝对安全"],
        "check": "compliance_redline",
    },
}

# PRD expected section keyword mapping
SECTION_KEYWORDS: dict[str, list[str]] = {
    "疗效分析": ["疗效", "有效性", "临床终点", "ORR", "PFS", "OS"],
    "安全性分析": ["安全性", "不良反应", "AE", "SAE", "耐受性"],
    "作用机制": ["作用机制", "MOA", "靶点", "通路", "药理"],
    "经济性评估": ["经济性", "成本效益", "ICER", "QALY"],
    "流行病学背景": ["流行病学", "发病率", "患病率"],
    "用法用量": ["用法用量", "剂量", "给药方案"],
    "临床指南": ["指南", "推荐", "CSCO", "NCCN"],
}


# ---------------------------------------------------------------------------
# Evidence review logic (US1)
# ---------------------------------------------------------------------------


def _detect_info_points(requirement_text: str) -> list[str]:
    """Detect which information point types are mentioned in the requirement."""
    detected = []
    for info_type, keywords in INFO_POINTS.items():
        for kw in keywords:
            if kw in requirement_text:
                detected.append(info_type)
                break
    # If nothing detected, return generic dimensions
    if not detected:
        detected = ["覆盖度", "可信度", "时效性"]
    return detected


def _count_keyword_hits(info_type: str, evidence_contents: list[str]) -> int:
    """Count unique keyword hits for an info point type across all evidence."""
    keywords = INFO_POINTS.get(info_type, [])
    total_hits = 0
    for content in evidence_contents:
        for kw in keywords:
            if kw in content:
                total_hits += 1
    return total_hits


def _build_evidence_findings(
    info_points: list[str],
    evidence_contents: list[str],
    evidence_count: int,
) -> list[dict]:
    """Build findings for each info point in evidence review mode."""
    findings = []
    for ip in info_points:
        hits = _count_keyword_hits(ip, evidence_contents)
        if evidence_count == 0:
            status = "missing"
            confidence = 1.0
        elif hits >= 2:
            status = "covered"
            confidence = 0.95
        elif hits == 1:
            status = "partial"
            confidence = 0.7
        else:
            status = "missing"
            confidence = 0.9

        findings.append(
            Finding(
                target_point=ip,
                status=status,
                confidence=confidence,
                detail=_status_detail(ip, status, hits, "evidence"),
            ).model_dump()
        )
    return findings


def _judge_sufficiency(findings: list[dict]) -> Sufficiency:
    """Determine overall sufficiency from findings.

    Rules (per spec acceptance scenarios):
      - all covered → sufficient
      - ≥50% covered or partial → partial (may have some missing)
      - <50% covered or partial → insufficient
    """
    total = len(findings)
    if total == 0:
        return "insufficient"
    covered = sum(1 for f in findings if f["status"] == "covered")
    partial_count = sum(1 for f in findings if f["status"] == "partial")

    coverage_ratio = (covered + partial_count) / total

    if covered == total:
        return "sufficient"
    if coverage_ratio >= 0.5:
        return "partial"
    return "insufficient"


def _build_supplement_hints(
    findings: list[dict],
    info_points: list[str],
) -> list[dict]:
    """Build supplement hints for missing/partial info points, capped at 5."""
    hints = []
    for f_item in findings:
        if f_item["status"] in ("missing", "partial"):
            priority: Priority = "high" if f_item["status"] == "missing" else "medium"
            ip = f_item["target_point"]
            hints.append(
                SupplementHint(
                    information_type=_ip_to_type_key(ip),
                    priority=priority,
                    description=_ip_to_supplement_desc(ip),
                ).model_dump()
            )
    # Sort by priority then cap at 5 most critical
    priority_order = {"high": 0, "medium": 1, "low": 2}
    hints.sort(key=lambda h: priority_order.get(h["priority"], 9))
    return hints[:5]


def _status_detail(
    target: str,
    status: str,
    hits: int,
    mode: str,
) -> str:
    if mode == "evidence":
        labels = {
            "covered": f"证据覆盖了「{target}」相关内容，置信度高",
            "partial": f"证据部分覆盖「{target}」，但不够充分，仅 {hits} 条证据涉及",
            "missing": f"未找到覆盖「{target}」的证据片段",
        }
        return labels.get(status, status)
    return status


def _ip_to_type_key(info_point: str) -> str:
    mapping = {
        "疗效数据": "efficacy_data",
        "安全性数据": "safety_data",
        "作用机制": "mechanism_of_action",
        "经济性评估": "economic_evaluation",
        "流行病学数据": "epidemiology_data",
        "用法用量": "dosage_administration",
        "临床指南引用": "clinical_guideline",
        "头对头研究": "head_to_head_study",
    }
    return mapping.get(info_point, info_point)


def _ip_to_supplement_desc(info_point: str) -> str:
    templates = {
        "疗效数据": "建议补充 III 期临床试验的主要终点数据（如 CDR-SB、ORR、PFS/OS 等）",
        "安全性数据": "建议补充 III 期临床试验的安全性数据，重点关注不良事件发生率和严重程度",
        "作用机制": "建议补充药物的作用靶点和信号通路说明，可参考已发表的作用机制综述",
        "经济性评估": "建议补充药物经济学评估数据，包括成本效益分析或 ICER 值",
        "流行病学数据": "建议补充目标适应症的流行病学数据（发病率、患病率、疾病负担）",
        "用法用量": "建议补充药物的推荐剂量、给药方案和特殊人群用药说明",
        "临床指南引用": "建议补充相关临床指南的推荐意见（如 CSCO、NCCN 等）",
        "头对头研究": "建议补充与其他标准治疗方案的头对头对比研究数据",
    }
    return templates.get(
        info_point, f"建议补充与「{info_point}」相关的证据材料"
    )


def evidence_review(
    writing_requirement: str,
    evidence_fragments: list[dict],
) -> dict:
    """Execute evidence review (mock implementation)."""
    # Detect information points from requirement
    info_points = _detect_info_points(writing_requirement)
    # evidence_fragments may be dicts or EvidenceFragment objects
    evidence_contents = [
        ef.content if hasattr(ef, "content") else ef.get("content", "")
        for ef in evidence_fragments
    ]

    # Build findings
    findings = _build_evidence_findings(info_points, evidence_contents, len(evidence_fragments))

    # Judge sufficiency
    sufficiency = _judge_sufficiency(findings)
    ready_for_drafting = sufficiency == "sufficient"

    # Build supplement hints
    supplement_hints = _build_supplement_hints(findings, info_points)

    # Build overall assessment
    covered_count = sum(1 for f in findings if f["status"] == "covered")
    assessment = (
        f"证据审核完成：{sufficiency}。"
        f"{len(info_points)} 个需求信息点中，{covered_count} 个被充分覆盖。"
    )
    if sufficiency == "insufficient":
        assessment += " 建议补充缺失证据后重新审核。"
    elif sufficiency == "partial":
        assessment += " 部分信息点覆盖不足，建议补充后进入撰写。"
    else:
        assessment += " 证据充分，可进入 PRD 撰写阶段。"

    return {
        "sufficiency": sufficiency,
        "findings": findings,
        "supplement_hints": supplement_hints,
        "ready_for_drafting": ready_for_drafting,
        "overall_assessment": assessment,
    }


# ---------------------------------------------------------------------------
# PRD review logic (US2)
# ---------------------------------------------------------------------------


def _parse_prd_sections(prd_content: str) -> dict[str, str]:
    """Parse PRD Markdown into sections by heading."""
    sections: dict[str, str] = {}
    lines = prd_content.split("\n")
    current_section = "__preamble__"
    current_content = []

    for line in lines:
        if line.startswith("#"):
            if current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = line.lstrip("#").strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_section] = "\n".join(current_content)

    return sections


def _detect_claims_without_evidence(section_text: str) -> list[str]:
    """Detect assertive statements without citation markers."""
    issues = []
    sentences = section_text.replace("。", "。\n").split("\n")
    for sent in sentences:
        sent = sent.strip()
        if not sent or len(sent) < 20:
            continue
        # Assertive language patterns (multi-char to reduce false positives)
        assert_patterns = ["显著改善", "显著降低", "明显优于", "有效改善", "安全可控"]
        has_assertion = any(p in sent for p in assert_patterns)
        has_citation = any(
            marker in sent for marker in ["[", "（来源", "PMID", "doi", "参考文献", "来源"]
        )
        if has_assertion and not has_citation:
            issues.append(sent[:60] + ("..." if len(sent) > 60 else ""))
    return issues


def _check_logic_transitions(sections: dict[str, str]) -> list[str]:
    """Check for missing transitions between sections."""
    issues = []
    section_names = list(sections.keys())
    if len(section_names) <= 1:
        return issues
    for i in range(len(section_names) - 1):
        prev_text = sections.get(section_names[i], "")
        next_text = sections.get(section_names[i + 1], "")
        # Skip if either section is very short (likely not a substantive section)
        if len(prev_text) < 30 or len(next_text) < 30:
            continue
        # Check if previous section ends with transition language
        transition_words = ["综上所述", "接下来", "在此基础上", "进一步"]
        if not any(tw in prev_text[-200:] for tw in transition_words):
            issues.append(
                f"「{section_names[i]}」到「{section_names[i+1]}」之间缺少过渡衔接"
            )
    return issues


def _check_structure_completeness(
    sections: dict[str, str],
    writing_requirement: str = "",
) -> list[str]:
    """Check if expected sections are present, based on writing requirement context."""
    # Determine which sections to expect from the writing requirement
    expected_sections = []
    for expected, keywords in SECTION_KEYWORDS.items():
        if any(kw in writing_requirement for kw in keywords):
            expected_sections.append(expected)

    # If requirement doesn't specify sections, skip this check
    if not expected_sections:
        return []

    missing = []
    section_text_combined = "\n".join(sections.keys()) + "\n" + "\n".join(
        s[:50] for s in sections.values()
    )
    for expected in expected_sections:
        keywords = SECTION_KEYWORDS.get(expected, [expected])
        if not any(kw in section_text_combined for kw in keywords):
            missing.append(expected)
    return missing


def _check_compliance_redlines(prd_content: str) -> list[str]:
    """Check for compliance red-line language."""
    issues = []
    redline_keywords = DEFECT_PATTERNS["合规红线"]["keywords"]
    for kw in redline_keywords:
        if kw in prd_content:
            issues.append(f"检测到合规敏感用语：「{kw}」，请核实是否符合医学内容规范")
    return issues


def _build_prd_findings(
    defect_results: dict,
) -> list[dict]:
    """Build findings from PRD defect detection results."""
    findings = []

    # Claim without evidence
    for claim_issue in defect_results.get("claims_without_evidence", []):
        findings.append(
            Finding(
                target_point="论证有据性",
                status="issue",
                confidence=0.85,
                detail=f"发现缺乏证据支撑的断言语句：{claim_issue}",
                suggestion="请为关键断言补充证据引用或来源标注",
            ).model_dump()
        )

    # Logic gaps
    for logic_issue in defect_results.get("logic_gaps", []):
        findings.append(
            Finding(
                target_point="逻辑贯通性",
                status="issue" if "缺少" in logic_issue else "ok",
                confidence=0.8,
                detail=logic_issue,
                suggestion="建议添加承上启下的过渡段落",
            ).model_dump()
        )

    # Structure missing
    for missing_section in defect_results.get("structure_missing", []):
        findings.append(
            Finding(
                target_point=f"结构完整性 — {missing_section}",
                status="issue",
                confidence=0.9,
                detail=f"预期章节「{missing_section}」未在 PRD 草稿中找到",
                suggestion=f"建议补充「{missing_section}」相关章节内容",
            ).model_dump()
        )

    # Compliance
    for compliance_issue in defect_results.get("compliance_issues", []):
        findings.append(
            Finding(
                target_point="合规红线",
                status="critical",
                confidence=0.95,
                detail=compliance_issue,
                suggestion="请根据医学合规要求修改相关内容",
            ).model_dump()
        )

    # If no findings at all, create a positive finding
    if not findings:
        findings.append(
            Finding(
                target_point="整体质量",
                status="ok",
                confidence=0.9,
                detail="PRD 草稿通过了全部审核维度检查",
            ).model_dump()
        )

    return findings


def _build_rewrite_targets(
    defect_results: dict,
    sections: dict[str, str],
) -> list[dict]:
    """Build rewrite targets from defect results."""
    targets = []

    for claim_issue in defect_results.get("claims_without_evidence", []):
        # Map claim to the most likely section
        section = "整体"
        for sec_name, sec_text in sections.items():
            if claim_issue[:20] in sec_text:
                section = sec_name
                break
        targets.append(
            RewriteTarget(
                section=section,
                severity="high",
                issue=f"存在无证据支撑的断言",
                target="为关键断言补充证据引用或降低断言强度，修改后使论证有据可依",
            ).model_dump()
        )

    for missing_section in defect_results.get("structure_missing", []):
        targets.append(
            RewriteTarget(
                section=missing_section,
                severity="high",
                issue=f"缺少「{missing_section}」章节",
                target=f"补充「{missing_section}」章节内容，确保 PRD 结构完整",
            ).model_dump()
        )

    for compliance_issue in defect_results.get("compliance_issues", []):
        targets.append(
            RewriteTarget(
                section="整体",
                severity="critical",
                issue=compliance_issue,
                target="移除或修改涉及合规红线的表述，确保内容符合医学传播规范",
            ).model_dump()
        )

    return targets


def prd_review(writing_requirement: str, prd_content: str) -> dict:
    """Execute PRD review (mock implementation)."""
    sections = _parse_prd_sections(prd_content)

    defect_results: dict[str, list[str]] = {}

    # Check claims without evidence
    all_text = prd_content
    claims = _detect_claims_without_evidence(all_text)
    if claims:
        defect_results["claims_without_evidence"] = claims

    # Check logic transitions
    logic_gaps = _check_logic_transitions(sections)
    if logic_gaps:
        defect_results["logic_gaps"] = logic_gaps

    # Check structure completeness
    structure_missing = _check_structure_completeness(sections, writing_requirement)
    if structure_missing:
        defect_results["structure_missing"] = structure_missing

    # Check compliance redlines
    compliance_issues = _check_compliance_redlines(all_text)
    if compliance_issues:
        defect_results["compliance_issues"] = compliance_issues

    # Build findings and rewrite targets
    findings = _build_prd_findings(defect_results)

    # Content sufficiency check: near-empty PRD is always revision_required
    content_text = "".join(sections.values()).strip()
    if len(content_text) < 100:
        findings.append(
            Finding(
                target_point="内容完整性",
                status="issue",
                confidence=1.0,
                detail="PRD 内容过短或仅含标题，不足以构成完整的 PRD 草稿",
                suggestion="请补充各章节内容，确保信息完整",
            ).model_dump()
        )

    rewrite_targets = _build_rewrite_targets(defect_results, sections)

    # Determine verdict
    has_critical = any(f["status"] == "critical" for f in findings)
    has_issue = any(f["status"] == "issue" for f in findings)
    if has_critical or has_issue:
        verdict: Verdict = "revision_required"
    else:
        verdict = "passed"

    ready_for_handoff = verdict == "passed"

    # Truncation warning
    warnings = []
    if len(prd_content) > 50000:
        warnings.append("PRD 超过 50000 字符，未逐句审核全文")

    # Overall assessment
    total_issues = len(findings)
    ok_count = sum(1 for f in findings if f["status"] == "ok")
    assessment = (
        f"PRD 审核完成：{verdict}。"
        f"{total_issues} 条审核发现中，{ok_count} 项通过，{total_issues - ok_count} 项需关注。"
    )
    if verdict == "revision_required":
        assessment += " 请根据改写目标修改后重新提交审核。"

    return {
        "verdict": verdict,
        "findings": findings,
        "rewrite_targets": rewrite_targets,
        "ready_for_handoff": ready_for_handoff,
        "overall_assessment": assessment,
        "warnings": warnings,
    }
