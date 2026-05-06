# Research: 003-product-review-skill

**Date**: 2026-05-06

## R1: Mock 审核逻辑实现方式

### Decision
基于规则的关键词匹配（rule-based keyword matching），不使用 ML/LLM。

### Rationale
- Mock 的核心约束是**确定性**（FR-014），相同输入必须产生相同输出。规则匹配天然确定性。
- 不引入外部依赖，保持 Skill 轻量（FR-012）。
- 规则匹配在 <1s 内完成（SC-001），远超 LLM 延迟。

### Implementation approach
1. 预定义 8 类「需求信息点类型」及其关键词映射
2. 预定义 4 类「PRD 缺陷模式」及其检测规则
3. 证据审核：对每个检测到的需求信息点，检查证据片段中的关键词覆盖率
4. PRD 审核：对 PRD 草稿逐章节匹配缺陷模式

### Alternatives considered
- **LLM-based mock**: 引入不确定性，违反 FR-014；延迟 >1s，违反 SC-001。
- **Simple always-pass mock**: 无实际检验价值，Pipeline 联调无法验证逻辑路径。
- **Regex-based**: 对中文自然语言支持差，关键词匹配更灵活。

---

## R2: Schema 与审核逻辑的解耦方式

### Decision
三层文件分离：`schema.py`（纯数据结构）、`reviewer.py`（审核逻辑）、`main.py`（入口编排）。

### Rationale
- FR-013 要求 schema 独立模块。三层分离后，同事只需替换 `reviewer.py` 内部实现。
- 与现有 Skill（cang_tag_search、input_structure）的模块化模式一致。
- `schema.py` 零业务逻辑依赖，可独立做单元测试和 schema 校验。

### File responsibilities
| 文件 | 职责 | 同事可否修改 |
|------|------|-------------|
| `schema.py` | Pydantic models + 枚举定义 | ❌ 不可改（接口契约） |
| `reviewer.py` | 审核逻辑实现（mock 或真实） | ✅ 可替换内部实现 |
| `main.py` | 输入校验 + 调度 reviewer + 输出组装 | ❌ 不可改（编排契约） |

### Alternatives considered
- **单文件**: schema 和逻辑混在一起，同事替换时容易误改 schema。
- **抽象基类**: 过度设计。Mock 阶段不需要 OOP 抽象层，一个函数替换更简单。

---

## R3: 需求信息点检测策略

### Decision
从写作需求的 Markdown 中提取章节标题和关键段落，与预定义的信息点类型关键词做匹配。

### Predefined information point types
| 类型 | 关键词 |
|------|--------|
| 疗效数据 | 疗效、有效率、ORR、PFS、OS、缓解率、临床终点 |
| 安全性数据 | 安全性、不良反应、不良事件、AE、SAE、耐受性 |
| 作用机制 | 机制、MOA、靶点、通路、药理 |
| 经济性评估 | 经济性、成本效益、ICER、QALY、药物经济学 |
| 流行病学数据 | 流行病学、发病率、患病率、流行病学 |
| 用法用量 | 用法、用量、剂量、给药方案、给药方式 |
| 临床指南引用 | 指南、推荐、CSCO、NCCN、共识 |
| 头对头研究 | 头对头、对比研究、对照试验、vs |

### Detection algorithm (mock)
1. 解析 Markdown，提取标题和段落
2. 对每个信息点类型，扫描全文是否出现其关键词
3. 出现 ≥1 个关键词 → 该信息点被识别为「需求关注点」
4. 未识别到任何信息点 → 默认返回通用审核维度（覆盖度/可信度/时效性）

### Alternatives considered
- **NLP 实体识别**: 依赖外部模型，违反 mock 约束。
- **让调用方显式传入信息点列表**: 增加上游负担，mock 阶段自动检测更实用。

---

## R4: 证据片段覆盖率计算

### Decision
对每个已识别的需求信息点，逐一检查证据片段列表中的关键词命中情况。三档判定：
- `covered`: ≥2 条证据命中该信息点关键词
- `partial`: 1 条证据命中
- `missing`: 0 条证据命中

### Sufficiency 综合判定
- `sufficient`: 所有信息点 `covered`
- `partial`: ≥50% 信息点 `covered` 或 `partial`，无 `missing`
- `insufficient`: 存在 `missing` 或 <50% 覆盖率

### Alternatives considered
- **语义相似度（embedding）**: 引入 numpy/sklearn，过重且非确定性。
- **全部标记 covered**: 无实际检验价值。

---

## R5: PRD 缺陷检测策略

### Decision
基于 4 类预定义缺陷模式，对 PRD Markdown 逐章节检测。

| 缺陷模式 | 检测规则（mock） | severity |
|----------|-----------------|----------|
| 论证无据 | 段落含断言性语句但未引用证据编号/来源标记 | high |
| 逻辑跳跃 | 章节间缺少过渡或因果关系链断裂（检测连接词缺失） | medium |
| 结构缺失 | 缺少预期章节（通过标题关键词匹配判断） | high |
| 合规红线 | 含超适应症/绝对化用语等敏感词 | critical |

### Verdict 综合判定
- `passed`: 无 high/critical 级 finding
- `revision_required`: 存在 high/critical 级 finding

### Alternatives considered
- **逐句文法分析**: 需 NLP 模型，违反 mock 约束。
- **仅检查结构完整性**: 过于单薄，mock 阶段联调价值低。

---

## R6: 测试策略

### Decision
四层测试：schema 校验 → 单元测试（mock reviewer）→ 确定性测试 → 集成测试。

| 测试层 | 内容 | 工具 |
|--------|------|------|
| Schema 校验 | 输入/输出 Pydantic 模型的正/反例验证 | pytest + pydantic |
| 单元测试 | Mock reviewer 各模式的规则覆盖 | pytest |
| 确定性测试 | 同一输入 10 次调用，验证输出完全一致 | pytest |
| 集成测试 | 完整调用链路（main.review()），按 Acceptance Scenarios 验证 | pytest |

### Test fixture design
- `fixtures/evidence_review/`: 充分/部分/不充分三种证据集 + 对应写作需求
- `fixtures/prd_review/`: 通过/需返修两种 PRD + 对应写作需求
- `fixtures/edge_cases/`: 空输入、无效模式、超大 PRD、格式异常证据

---

## R7: 契约版本控制

### Decision
在 `ReviewResult` 中包含 `schema_version` 字段（字符串，格式 `"1.0"`）。

### Rationale
- 同事替换内部实现时如需扩展 schema，必须升级版本号。
- Pipeline 可通过版本号做兼容性判断。
- 遵循语义化版本精神：主版本号变更表示不兼容改动。

### Version policy
- `1.0`: 初始 mock 版本
- `1.x`: 同事扩展字段（向后兼容）
- `2.0`: 同事做不兼容的 schema 变更（需 Pipeline 适配）
