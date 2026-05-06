# Feature Specification: 产品审核子 Agent Skill

**Feature Branch**: `003-product-review-skill`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "产品 Agent 的审核子 Agent，提供证据审核和 PRD 审核两种模式。内部实现由同事负责，当前以 mock 状态构建（真实 schema + mock 逻辑），定义清晰的输入输出契约。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 证据审核：判断提取到的证据是否充分覆盖写作需求 (Priority: P1)

产品 Agent 从藏经阁检索并提取证据片段后，调用审核子 Agent 对证据做充分性审核。审核子 Agent 逐条检查写作需求中的关键信息点是否被证据覆盖，输出「充分/部分充分/不充分」判定。当证据不充分时，生成具体的补充建议，指导人类用户补充材料。人类用户根据审核结果决定是进入补充循环还是确认进入撰写。

**Why this priority**: 证据审核是产品 Agent 闭环的第一道质量门。没有它，不充分的证据会直接进入撰写，导致 PRD 质量不可控。它是「证据提取→审核→补充循环」的核心裁判。

**Independent Test**: 传入一个写作需求（如"写一篇仑卡奈单抗的科普文章"）和一组模拟证据片段，Skill 返回包含 sufficiency 判定、逐条 findings、supplement_hints 的结构化审核结果。可独立验证：给定明显不充分的证据时返回 `insufficient`；给定充分覆盖的证据时返回 `sufficient`。

**Acceptance Scenarios**:

1. **Given** 写作需求包含「疗效数据」「安全性数据」「作用机制」三个关键信息点，且传入的证据只覆盖了「疗效数据」和「作用机制」，**When** 调用证据审核模式，**Then** 返回 `sufficiency: "partial"`，findings 中「安全性数据」标记为 `missing` 并附补充建议
2. **Given** 写作需求包含「疗效数据」「安全性数据」两个关键信息点，传入的证据全部覆盖且置信度高，**When** 调用证据审核模式，**Then** 返回 `sufficiency: "sufficient"`，`ready_for_drafting: true`
3. **Given** 写作需求包含「疗效数据」「安全性数据」「经济性评估」三个关键信息点，传入的证据仅覆盖「疗效数据」且置信度低，**When** 调用证据审核模式，**Then** 返回 `sufficiency: "insufficient"`，supplement_hints 中明确指出缺失的信息类型和建议方向
4. **Given** 传入的证据片段为空列表，**When** 调用证据审核模式，**Then** 返回 `sufficiency: "insufficient"`，所有需求点标记为 `missing`，不崩溃

---

### User Story 2 - PRD 审核：审核撰写完成的 PRD 草稿质量 (Priority: P2)

产品 Agent 完成 PRD 撰写后，调用审核子 Agent 对 PRD 草稿做质量审核。审核维度包括：逻辑是否贯通、论证是否有据可依、是否存在合规红线（医学内容专属）、结构是否完整。审核结果输出通过/返修判定及具体改写目标。人类用户根据审核结果决定是确认交付还是启动修改。

**Why this priority**: PRD 审核是产品 Agent 交付给写作 Agent 前的最后一道质量门。证据审核先做（P1），PRD 审核后做（P2），两阶段审核确保产品 Agent 输出质量。

**Independent Test**: 传入一份 PRD 草稿和原始写作需求，Skill 返回包含 verdict（passed/revision_required）、逐条 findings、rewrite_targets 的结构化审核结果。可独立验证：传入有明显逻辑缺陷的 PRD 时返回 `revision_required` 并指明问题所在。

**Acceptance Scenarios**:

1. **Given** PRD 草稿中各章节均与写作需求对应、论证有据、无合规问题，**When** 调用 PRD 审核模式，**Then** 返回 `verdict: "passed"`，`ready_for_handoff: true`
2. **Given** PRD 草稿中存在论证跳跃（某章节结论无证据支撑），**When** 调用 PRD 审核模式，**Then** 返回 `verdict: "revision_required"`，对应 finding 的 severity 标记为 `high`，rewrite_targets 中包含该章节的具体改写目标
3. **Given** PRD 草稿中存在合规红线问题（如超适应症表述），**When** 调用 PRD 审核模式，**Then** 对应 finding 的 severity 标记为 `critical`，`ready_for_handoff: false`
4. **Given** PRD 草稿内容为空或仅含标题，**When** 调用 PRD 审核模式，**Then** 返回 `verdict: "revision_required"`，明确标注内容不完整，不崩溃

---

### User Story 3 - Mock 模式：以确定性输出支持 Pipeline 联调 (Priority: P3)

产品 Agent Pipeline 的其他环节（补充循环、编排器）需要依赖审核子 Agent 的输出来完成集成。在同事实现真实审核逻辑之前，Skill 以 mock 模式运行：使用真实的输入输出 schema，但内部审核逻辑基于简单的规则匹配（如关键词匹配、需求点计数），输出在输入固定时具有确定性。

**Why this priority**: Mock 模式保证 Pipeline 其他环节不被阻塞。它是管道联调的前提条件，但本身不直接产生用户价值，因此 P3。

**Independent Test**: 固定输入调用 Skill 两次，两次输出完全一致（确定性）。Schema 校验工具可以验证输出符合定义的 JSON Schema。

**Acceptance Scenarios**:

1. **Given** 相同的审核请求被调用两次，**When** 两次调用之间无任何配置变更，**Then** 两次输出完全一致
2. **Given** Skill 的任一模式被调用，**When** 对返回值做 schema 校验，**Then** 所有必填字段存在且类型正确
3. **Given** 同事拿到 Skill 代码后只修改 `review()` 函数内部实现，**When** 修改后的 Skill 运行，**Then** Pipeline 其他环节无需任何改动即可正常工作

---

### Edge Cases

- **空输入保护**：写作需求为空或仅含空白字符时，返回错误说明（非崩溃），标注 `error: "empty_requirement"`
- **证据片段格式异常**：证据片段列表中某个元素缺少必要字段（如 content 为空），该条目标注为 `skipped` 并计入 warning，继续审核其余证据
- **PRD 草稿过长（>50000 字符）**：正常审核，但在结果中标注 `truncated_review: true` 表示可能未逐句审核全文
- **审核模式无效**：传入无效的 mode 值（非 `evidence_review` 或 `prd_review`），返回明确错误，不执行任何审核逻辑
- **证据与需求语言不匹配**：需求为中文但证据为英文时正常审核（mock 阶段以关键词匹配兜底）
- **重复调用**：同一审核请求短时间内被重复调用，输出保持一致（幂等）
- **supplement_hints 数量上限**：当缺失信息点过多（>10 个），supplement_hints 只返回最关键的 5 个并标注 `更多省略`
- **同事替换 mock 后的兼容性**：Schema 字段的增删必须有版本号控制，避免 Pipeline 断裂

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Skill MUST 支持两种审核模式：`evidence_review`（证据审核）和 `prd_review`（PRD 审核），通过 `mode` 参数切换
- **FR-002**: Skill MUST 接收写作需求（`writing_requirement`，结构化 Markdown 字符串）作为必填输入
- **FR-003**: 证据审核模式下，Skill MUST 接收 `evidence_fragments`（证据片段列表），每项至少包含 `content` 和 `source` 字段
- **FR-004**: PRD 审核模式下，Skill MUST 接收 `prd_content`（PRD 草稿内容，Markdown 字符串）
- **FR-005**: 证据审核模式下，Skill MUST 输出 `sufficiency` 字段，取值为 `"sufficient"` | `"partial"` | `"insufficient"`
- **FR-006**: PRD 审核模式下，Skill MUST 输出 `verdict` 字段，取值为 `"passed"` | `"revision_required"`
- **FR-007**: Skill MUST 输出 `findings` 数组，每项包含 `target_point`（审核目标点）、`status`（证据模式：covered/partial/missing；PRD 模式：ok/issue/critical）、`confidence`（0.0-1.0）、`detail`（自然语言说明）
- **FR-008**: 证据审核模式下，Skill MUST 输出 `supplement_hints` 数组，列出建议补充的信息类型和方向
- **FR-009**: PRD 审核模式下，Skill MUST 输出 `rewrite_targets` 数组，每项包含 `section`（目标章节）、`severity`（high/medium/low/critical）、`issue`（问题描述）、`target`（改写目标说明）
- **FR-010**: 证据审核模式下，Skill MUST 输出 `ready_for_drafting`（布尔值），指示证据是否充分到可以进入撰写阶段
- **FR-011**: PRD 审核模式下，Skill MUST 输出 `ready_for_handoff`（布尔值），指示 PRD 是否可以交付给写作 Agent
- **FR-012**: Skill MUST 以 mock 逻辑实现内部审核（基于规则匹配），不使用外部 LLM 调用或外部服务
- **FR-013**: Skill 的输入输出 schema MUST 定义为独立模块（Pydantic models），与审核逻辑解耦，确保同事替换内部实现时 schema 不变
- **FR-014**: 相同的输入在相同配置下 MUST 产生相同的输出（确定性/幂等）
- **FR-015**: Skill MUST 在输入无效时（空需求、无效模式）返回结构化错误而非抛出未捕获异常

### Key Entities

**核心实体**（5 个，定义审核请求和结果的结构）：

- **ReviewRequest**: 一次审核请求。包含：`mode`（审核模式）、`writing_requirement`（写作需求，Markdown）、`evidence_fragments`（证据片段列表，证据模式必填）、`prd_content`（PRD 草稿，PRD 模式必填）、`config`（可选配置，如 strictness 严格度）
- **ReviewResult**: 一次审核结果。包含：`mode`、`schema_version`、`sufficiency` 或 `verdict`（取决于模式）、`findings`、`overall_assessment`（整体评估文本）、`supplement_hints`（证据模式）、`rewrite_targets`（PRD 模式）、`ready_for_drafting` 或 `ready_for_handoff`、`warnings`（非阻塞问题清单）
- **Finding**: 单条审核发现。包含：`target_point`（审核关注点）、`status`（证据模式：covered/partial/missing；PRD 模式：ok/issue/critical）、`confidence`（0.0-1.0，当前 mock 模式为 1.0 或规则计算值）、`detail`（说明文本）、`suggestion`（可选，改进建议）
- **SupplementHint**: 补充建议（仅证据审核模式）。包含：`information_type`（信息类型，如 efficacy_data/safety_data）、`priority`（high/medium/low）、`description`（具体补充方向）
- **RewriteTarget**: 改写目标（仅 PRD 审核模式）。包含：`section`（目标章节名称）、`severity`（high/medium/low/critical）、`issue`（问题描述）、`target`（改写目标说明）

**辅助实体**（3 个，支撑请求结构和错误处理）：

- **EvidenceFragment**: 证据片段。包含：`content`（证据文本）、`source`（来源标识）、`theme`（可选，主题标注）
- **ReviewConfig**: 审核配置。包含：`strictness`（"standard" | "strict"，默认 "standard"）
- **ReviewError**: 输入校验失败的结构化错误。包含：`error`（错误码）、`message`（人类可读说明）

完整字段定义和校验规则见 [data-model.md](./data-model.md)。

### Interface Contract (👤 同事依赖项)

以下 schema 是 Skill 与同事实现之间的接口契约。**同事只需实现 `review()` 函数内部逻辑，输入输出 schema 保持不变。**

```
# 输入（两种模式共用外层结构）
ReviewRequest {
    mode: "evidence_review" | "prd_review"
    writing_requirement: str          # 结构化 Markdown（来自 input_structure）
    evidence_fragments: [             # mode=evidence_review 时必填
        { content: str, source: str, theme?: str }
    ] | None
    prd_content: str | None           # mode=prd_review 时必填
    config: {
        strictness: "standard" | "strict" = "standard"
    }
}

# 输出（两种模式共用外层结构）
ReviewResult {
    mode: "evidence_review" | "prd_review"

    # 证据审核模式专属
    sufficiency: "sufficient" | "partial" | "insufficient" | None
    supplement_hints: [SupplementHint] | None
    ready_for_drafting: bool | None

    # PRD 审核模式专属
    verdict: "passed" | "revision_required" | None
    rewrite_targets: [RewriteTarget] | None
    ready_for_handoff: bool | None

    # 通用
    findings: [Finding]
    overall_assessment: str
    warnings: [str]
}
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 一次审核请求（含 5 条证据片段，3000 字符写作需求）在 1 秒内返回结果（mock 模式下纯逻辑运算，不含网络/LLM 调用）
- **SC-002**: Schema 校验覆盖率达到 100%——所有必填输入字段缺失时返回明确错误，所有输出字段的类型和枚举值与 Schema 定义一致
- **SC-003**: 同一输入连续调用 10 次，输出 100% 一致（确定性验证）
- **SC-004**: 证据审核模式下，传入「缺失关键信息点」的证据集时，`sufficiency` 准确反映为 `insufficient` 且 `supplement_hints` 非空（mock 规则覆盖 100% 的预定义需求点模式）
- **SC-005**: PRD 审核模式下，传入包含已知缺陷（如缺少论证、合规问题）的 PRD 时，`verdict` 准确反映为 `revision_required` 且 `rewrite_targets` 非空（mock 规则覆盖 100% 的预定义问题模式）
- **SC-006**: 同事替换 mock 实现时，仅需修改 `<review_internal>` 模块，不影响 Pipeline 其他环节（通过代码审查验证）

## Assumptions

- 产品审核子 Agent 是同步调用（和 input_structure、cang_tag_search 一样），不涉及异步队列或网络通信
- Mock 模式的规则匹配基于中文关键词，预定义了一系列「需求信息点类型」（8 类）和「PRD 缺陷模式」（4 类），详见 [research.md](./research.md) R3/R5
- 👤 **同事负责部分**：真实审核逻辑的实现（替换 mock 模块），可能涉及 LLM 调用、藏经阁规则库（L1-L4）匹配、或自定义审核算法
- Skill 的输入来源于上游（input_structure 的结构化 Markdown、cang_tag_search 的标签匹配结果），不直接面向终端用户
- 产品 Agent 编排器负责调用顺序和人类确认节点的交互，Skill 本身只做审核判定
- 初次实现不包含「增量审核」（只审核与上一轮相比的变化部分），每轮都是全量审核
- Spec 输出的 PRD 内容为 Markdown 格式，章节以 heading 划分，便于审核时定位

## Clarifications

### Session 2026-05-06

- **Q1**: 产品审核子 Agent 的内部实现逻辑目前不清楚，如何处理？ → **A**: 以 mock 状态先行实现，使用真实 schema + 基于规则的 mock 内部逻辑（关键词匹配 + 需求点计数）。Schema 定义在独立模块中，与审核逻辑解耦。同事后续只需替换 mock 内部实现，接口契约和外层 Pipeline 保持不变。FR-012、FR-013 明确此项约束。
- **Q2**: 证据审核和 PRD 审核的判定维度有什么不同？ → **A**: 证据审核关注「覆盖度」——写作需求中的关键信息点是否被证据支撑（sufficiency: sufficient/partial/insufficient）。PRD 审核关注「质量」——逻辑贯通性、论证有据、合规性、结构完整性（verdict: passed/revision_required）。两种模式共享 Finding 结构但 status 枚举值不同。
- **Q3**: 输出中的补充建议/改写目标和人类确认节点如何交互？ → **A**: Skill 只产出结构化的审核结果（supplement_hints / rewrite_targets）。人类确认节点的交互逻辑由上层「产品 Agent 编排器」负责实现，不属于本 Skill 的范围。
