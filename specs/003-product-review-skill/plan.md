# Implementation Plan: 产品审核子 Agent Skill

**Branch**: `003-product-review-skill` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/003-product-review-skill/spec.md`

## Summary

构建一个 Claude Skill（`product-review`），为产品 Agent 提供证据审核和 PRD 审核两种能力。当前以 mock 模式实现（真实 Pydantic schema + 规则匹配逻辑），同事后续替换 `reviewer.py` 内部实现即可完成升级。纯同步调用，无外部依赖。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Pydantic 2.x（唯一依赖，用于 schema 定义和校验）
**Storage**: N/A（无状态纯函数）
**Testing**: pytest
**Target Platform**: Linux server
**Project Type**: Claude Skill (Python library with importable entry point)
**Performance Goals**: <1s 单次审核（mock 模式，纯规则匹配）
**Constraints**: 确定性输出（相同输入 → 相同输出），schema 与逻辑解耦，无外部 LLM/API 调用
**Scale/Scope**: 2 种审核模式，5 个核心实体，15 个 FR，8 类信息点模式，4 类缺陷模式

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I - Protected Master Branch
- [x] Feature branch `003-product-review-skill` 从 main 创建（注意：项目无 git 仓库，此为逻辑分支标识）
- [x] 遵循 `###-feature-name` 命名规范

### Principle II - Feature Branch Workflow
- [x] Plan 文档记录目标实现路径
- [x] 无直接对 main 的提交

### Principle III - Dual Environment Deployment
- [x] Skill 为文件级部署（复制到 `.claude/skills/product-review/`），无端口冲突
- [x] 开发环境：本地 pytest 验证

### Principle IV - Deployment Gatekeeping
- [x] Skill 无 `deploy.sh` 依赖，纯文件部署
- [x] 文件变更通过 spec 文档追踪

### Principle V - Minimum Invasive Changes
- [x] 唯一新依赖 `pydantic` 已在 cang_tag_search 中使用，非首次引入
- [x] 无数据库变更（无状态 Skill）
- [x] 遵循现有 Skill 模式（参考：cang_tag_search、input_structure）
- [x] 不引入新的架构模式

**Complexity Tracking**: No violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-product-review-skill/
├── plan.md              # This file
├── research.md          # Phase 0: Technical decisions
├── data-model.md        # Phase 1: Entities and data structures
├── quickstart.md        # Phase 1: Quick start guide
├── contracts/           # Phase 1: Public API contract
│   └── skill-api.md
└── tasks.md             # Phase 2: /speckit.tasks output
```

### Source Code (repository root: `.claude/skills/product-review/`)

```text
.claude/skills/product-review/
├── SKILL.md              # Skill description (for Claude discovery)
├── __init__.py           # Package init, exports review()
├── main.py               # Entry point + input validation + orchestrates reviewer
├── schema.py             # 👤 不可改 — Pydantic models (ReviewRequest, ReviewResult, Finding, etc.)
├── reviewer.py           # 👤 可替换 — Mock review logic (keyword matching)
├── requirements.txt      # pydantic>=2.0.0
└── test/
    ├── fixtures/
    │   ├── evidence_review/
    │   │   ├── sufficient_evidence.json
    │   │   ├── partial_evidence.json
    │   │   └── insufficient_evidence.json
    │   ├── prd_review/
    │   │   ├── passed_prd.json
    │   │   └── revision_prd.json
    │   └── edge_cases/
    │       ├── empty_requirement.json
    │       ├── invalid_mode.json
    │       └── malformed_evidence.json
    ├── test_schema.py          # Schema validation tests
    ├── test_evidence_review.py # 证据审核模式单元测试
    ├── test_prd_review.py      # PRD 审核模式单元测试
    ├── test_determinism.py     # 确定性/幂等测试
    └── test_integration.py     # 集成测试（完整调用链）
```

**Structure Decision**: 三层文件分离（`schema.py` / `reviewer.py` / `main.py`）确保同事替换 reviewer 时不触及 schema 和入口逻辑。遵循现有 Skill 目录模式。

## Implementation Phases

### Phase 0: Foundation（schema + 项目骨架）

1. 创建 `.claude/skills/product-review/` 目录结构
2. 编写 `requirements.txt`
3. 编写 `schema.py` — 所有 Pydantic models + 枚举 + 校验规则
4. 编写 `SKILL.md` — Skill 说明文档

### Phase 1: Mock Review Logic

5. 编写 `reviewer.py` — 信息点检测逻辑（8 类关键词映射）
6. 编写 `reviewer.py` — 证据覆盖率计算逻辑（covered/partial/missing 三档）
7. 编写 `reviewer.py` — PRD 缺陷检测逻辑（4 类缺陷模式）
8. 编写 `reviewer.py` — Sufficiency/Verdict 综合判定 + supplement_hints/rewrite_targets 生成

### Phase 2: Entry Point & Assembly

9. 编写 `main.py` — 输入校验（空需求、无效模式、缺失必填字段）
10. 编写 `main.py` — 调度 reviewer + 输出组装 + 错误返回
11. 编写 `__init__.py` — 导出 `review`

### Phase 3: Testing

12. 准备 test fixtures（充分/部分/不充分证据集，通过/返修 PRD，边界用例）
13. 编写 `test_schema.py` — Pydantic 模型正反例校验
14. 编写 `test_evidence_review.py` — 证据审核模式单元测试（按 Acceptance Scenarios）
15. 编写 `test_prd_review.py` — PRD 审核模式单元测试（按 Acceptance Scenarios）
16. 编写 `test_determinism.py` — 10 次调用输出一致性验证
17. 编写 `test_integration.py` — 端到端集成测试
18. 运行全量测试，验证覆盖率和通过率

## Estimated Complexity

| Module | Lines | Difficulty | 👤 Colleague Touch |
|--------|-------|------------|-------------------|
| schema.py | ~100 | Medium（Pydantic 枚举 + 校验） | ❌ 不可改 |
| reviewer.py | ~250 | Medium（规则匹配逻辑） | ✅ 可替换 |
| main.py | ~80 | Medium（编排 + 校验） | ❌ 不可改 |
| SKILL.md | ~50 | Low | ❌ 不可改 |
| test/ | ~350 | Low-Medium | ❌ 可能需要补 |
| **Total** | **~830** | | |
