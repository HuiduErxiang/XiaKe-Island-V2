# Skill API Contract: 产品审核子 Agent

**Version**: 1.0
**Date**: 2026-05-06

## Public Entry Point

```python
from product_review import review

result = review(
    mode="evidence_review",              # 或 "prd_review"
    writing_requirement="## 写作需求\n...",
    evidence_fragments=[...],             # mode=evidence_review 时必填
    # prd_content="...",                 # mode=prd_review 时必填
    config={"strictness": "standard"}    # 可选
)
```

`review()` 是 Skill 的唯一公开接口。所有参数为 keyword arguments。

## Parameters

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `mode` | `str` | ✅ | — | `"evidence_review"` 或 `"prd_review"` |
| `writing_requirement` | `str` | ✅ | — | 结构化 Markdown，来自 input_structure |
| `evidence_fragments` | `list[dict]` | 证据模式必填 | — | 每项含 `content`(str), `source`(str), `theme`(str, 可选) |
| `prd_content` | `str` | PRD 模式必填 | — | PRD 草稿 Markdown |
| `config` | `dict \| None` | ❌ | `None` | `{"strictness": "standard" \| "strict"}` |

## Return Value

返回 `ReviewResult` 字典：

```python
# 证据审核模式返回值
{
    "mode": "evidence_review",
    "schema_version": "1.0",
    "sufficiency": "partial",            # "sufficient" | "partial" | "insufficient"
    "ready_for_drafting": False,
    "supplement_hints": [
        {
            "information_type": "safety_data",
            "priority": "high",
            "description": "建议补充 III 期临床试验的安全性数据..."
        }
    ],
    "findings": [
        {
            "target_point": "疗效数据",
            "status": "covered",          # evidence: covered|partial|missing
            "confidence": 0.95,
            "detail": "证据覆盖了主要疗效终点数据...",
            "suggestion": None
        }
    ],
    "overall_assessment": "证据部分充分。疗效数据覆盖良好，但安全性数据缺失...",
    "warnings": []
}

# PRD 审核模式返回值
{
    "mode": "prd_review",
    "schema_version": "1.0",
    "verdict": "revision_required",       # "passed" | "revision_required"
    "ready_for_handoff": False,
    "rewrite_targets": [
        {
            "section": "安全性分析",
            "severity": "high",
            "issue": "该章节结论缺乏证据支撑",
            "target": "为安全性结论补充证据引用或降低断言强度"
        }
    ],
    "findings": [
        {
            "target_point": "逻辑贯通性",
            "status": "issue",            # prd: ok|issue|critical
            "confidence": 0.85,
            "detail": "疗效章节与安全性章节之间缺少过渡...",
            "suggestion": "建议添加承上启下的过渡段落"
        }
    ],
    "overall_assessment": "PRD 结构基本完整，但存在逻辑跳跃和论证不足...",
    "warnings": ["PRD 超过 50000 字符，未逐句审核全文"]
}
```

## Error Response

输入无效时返回错误：

```python
# 空需求
{"error": "empty_requirement", "message": "写作需求不能为空"}

# 无效模式
{"error": "invalid_mode", "message": "无效的审核模式 'xxx'，支持 evidence_review 或 prd_review"}

# 证据模式缺失 evidence_fragments
{"error": "missing_evidence", "message": "证据审核模式下 evidence_fragments 为必填参数"}
```

> **注意**: 错误以字典形式返回（非抛异常），遵循 FR-015。

## Mock Behavior Contract

Mock 模式下 `review()` 保证：

1. **确定性**：相同参数返回逐字节相同的输出
2. **无外部依赖**：不发起网络请求、不读取文件系统、不调用 LLM
3. **规则驱动**：审核逻辑仅基于预定义的关键词匹配
4. **Schema 完整**：所有必填字段始终存在

## Compatibility

- **Schema version**: 输出中 `schema_version` 标识契约版本
- **Backward compatibility**: 1.x 版本新增字段不删除已有字段
- **Breaking changes**: 主版本号递增（2.0+），需 Pipeline 适配

## 👤 Colleague Integration Point

同事替换 mock 实现时：

1. **可修改**: `reviewer.py` 内部实现（可替换为 LLM 调用、藏经阁规则匹配等）
2. **不可修改**: `schema.py`（数据模型）、`main.py`（入口编排）、`SKILL.md`（本文档规定的接口契约）
3. **如需扩展 schema**: 在 `schema.py` 中新增可选字段，升级 `schema_version` 小版本号（1.x），不删除已有字段
4. **如需不兼容变更**: 升级 `schema_version` 主版本号（2.0），同步更新 Pipeline
