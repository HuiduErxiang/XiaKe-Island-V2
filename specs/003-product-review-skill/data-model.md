# Data Model: 003-product-review-skill

**Date**: 2026-05-06

## Entity Overview

```
ReviewRequest ──→ review() ──→ ReviewResult
                      │
                      ├── Finding[]
                      ├── SupplementHint[]  (证据模式)
                      └── RewriteTarget[]   (PRD 模式)
```

## Entities

### ReviewRequest

一次审核请求。两种模式共用外层结构，模式专属字段通过 Optional 区分。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | `Literal["evidence_review", "prd_review"]` | ✅ | 审核模式 |
| `writing_requirement` | `str` | ✅ | 写作需求，结构化 Markdown |
| `evidence_fragments` | `list[EvidenceFragment] \| None` | 证据模式必填 | 证据片段列表 |
| `prd_content` | `str \| None` | PRD 模式必填 | PRD 草稿内容 |
| `config` | `ReviewConfig \| None` | ❌ | 审核配置 |

**Validation rules**:
- `mode="evidence_review"` → `evidence_fragments` 必填且非空
- `mode="prd_review"` → `prd_content` 必填且非空
- `writing_requirement` 不能为空或纯空白字符
- 无效 `mode` 值直接拒绝，不执行审核

### EvidenceFragment

证据片段（来自上游证据提取）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | `str` | ✅ | 证据文本内容 |
| `source` | `str` | ✅ | 来源标识（文件名/文献ID/URL） |
| `theme` | `str \| None` | ❌ | 主题标注（如"疗效数据"） |

### ReviewConfig

审核配置（可选）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `strictness` | `Literal["standard", "strict"]` | `"standard"` | 严格度。strict 模式下覆盖率阈值提高 |

### ReviewResult

一次审核的完整结果。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | `str` | ✅ | 审核模式（回显） |
| `schema_version` | `str` | ✅ | Schema 版本号（如 `"1.0"`） |
| `findings` | `list[Finding]` | ✅ | 审核发现列表 |
| `overall_assessment` | `str` | ✅ | 整体评估（自然语言） |
| `warnings` | `list[str]` | ✅ | 非阻塞警告（可空） |
| `sufficiency` | `Literal["sufficient", "partial", "insufficient"] \| None` | ❌ | 证据充分性（证据模式） |
| `supplement_hints` | `list[SupplementHint] \| None` | ❌ | 补充建议（证据模式） |
| `ready_for_drafting` | `bool \| None` | ❌ | 是否可进入撰写（证据模式） |
| `verdict` | `Literal["passed", "revision_required"] \| None` | ❌ | PRD 审核判定（PRD 模式） |
| `rewrite_targets` | `list[RewriteTarget] \| None` | ❌ | 改写目标（PRD 模式） |
| `ready_for_handoff` | `bool \| None` | ❌ | 是否可交付写作 Agent（PRD 模式） |

**Invariant**: 同一 mode 下，该 mode 的专属字段必非 None；另一 mode 的专属字段必为 None。

### Finding

单条审核发现。两种模式共享外层结构，`status` 枚举值按模式不同。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_point` | `str` | ✅ | 审核关注点名称（如"疗效数据"） |
| `status` | `str` | ✅ | 证据模式: `covered\|partial\|missing`；PRD 模式: `ok\|issue\|critical` |
| `confidence` | `float` | ✅ | 置信度 0.0-1.0 |
| `detail` | `str` | ✅ | 自然语言说明 |
| `suggestion` | `str \| None` | ❌ | 改进建议 |

### SupplementHint

补充建议（仅证据审核模式）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `information_type` | `str` | ✅ | 信息类型标识（如 `efficacy_data`） |
| `priority` | `Literal["high", "medium", "low"]` | ✅ | 优先级 |
| `description` | `str` | ✅ | 具体补充方向和说明 |

### RewriteTarget

改写目标（仅 PRD 审核模式）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `section` | `str` | ✅ | 目标章节名称 |
| `severity` | `Literal["critical", "high", "medium", "low"]` | ✅ | 问题严重度 |
| `issue` | `str` | ✅ | 问题描述 |
| `target` | `str` | ✅ | 改写目标说明 |

### ReviewError

输入校验失败时返回的结构化错误。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `error` | `str` | ✅ | 错误码（如 `empty_requirement`） |
| `message` | `str` | ✅ | 人类可读的错误说明 |

## State Transitions

本 Skill 为无状态函数，不涉及状态转换。审核判定结果传递给上游编排器处理。

## Validation Summary

| 规则 | 条件 |
|------|------|
| `mode` 有效性 | 必须为 `evidence_review` 或 `prd_review` |
| 证据模式输入 | `evidence_fragments` 非 None 且非空 |
| PRD 模式输入 | `prd_content` 非 None 且非空 |
| `writing_requirement` | 非空字符串（trim 后长度 >0） |
| `confidence` 范围 | 0.0 ≤ confidence ≤ 1.0 |
| `sufficiency` 枚举 | 仅 `sufficient/partial/insufficient` |
| `verdict` 枚举 | 仅 `passed/revision_required` |
| `severity` 枚举 | 仅 `critical/high/medium/low` |
| `priority` 枚举 | 仅 `high/medium/low` |
| 输出模式一致性 | 证据模式出 `sufficiency`/`supplement_hints`/`ready_for_drafting`；PRD 模式出 `verdict`/`rewrite_targets`/`ready_for_handoff` |
