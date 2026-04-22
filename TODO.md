# TODO - AI 写作系统待办事项

## Phase 1 · 数据来源层

- [ ] **藏经阁 API 接入** `src/data_layer/knowledge_base.py - ZangjinggeClient`
  - 确认藏经阁接口文档，实现 `get_all_tags()` 和 `get_articles_by_tag()`

- [ ] **标签简化模块** `src/data_layer/knowledge_base.py - TagSimplifier`
  - 实现标签清洗（去噪、去重、规范化命名）逻辑

- [ ] **KV 索引构建** `src/data_layer/knowledge_base.py - KVIndexBuilder`
  - 确定存储方案（内存 / Redis / 本地 JSON）
  - 实现 `build()` 全量拉取并构建索引

- [ ] **标签检索** `src/data_layer/knowledge_base.py - TagRetriever`
  - 实现意图 → 标签匹配算法（关键词匹配 / 向量检索）

- [ ] **证据提取 Skill** `src/data_layer/knowledge_base.py - EvidenceExtractSkill`
  - 实现从文章中精细抽取结构化证据片段

---

## Phase 2 · 产品 Agent

- [ ] **输入结构化 Skill** `src/agents/product_agent/skills/input_structure_skill.py`
  - 引入并实现 PDF 解析（PyPDF2 或 pdfminer）
  - 引入并实现 DOCX 解析（python-docx）
  - 引入并实现 PPT 解析（python-pptx）
  - 统一输出结构化 Markdown 格式

- [ ] **证据补充 Skill** `src/agents/product_agent/skills/evidence_supplement_skill.py`
  - 实现从 PRD 内容中提取检索意图
  - 调用 EvidenceExtractSkill 注入证据到 PRD

- [ ] **产品审核子 Agent** `src/agents/product_agent/skills/prd_review_skill.py - ProductReviewAgent`
  - 定义审核维度（完整性 / 逻辑性 / 需求覆盖度）
  - 实现审核后回写修改意见，触发迭代修正机制

---

## Phase 3 · 写作 Agent

- [ ] **写作 Skills** `src/agents/writing_agent/skills/writing_skills.py - WritingSkills`
  - 确定要接入的写作 Skill 列表（Speckit 技能组）
  - 实现多风格/类型的写作调用（informational / narrative / persuasive）

- [ ] **写作审核子 Agent** `src/agents/writing_agent/skills/draft_review_skill.py - WritingReviewAgent`
  - 定义审核维度（可读性 / 准确性 / 风格一致性）
  - 实现审核后回写修改意见，触发迭代修正机制

---

## Phase 4 · 工程化

- [ ] **Orchestrator 通信管理** `src/orchestrator/orchestrator.py`
  - 实现数据层 ↔ 执行 Agent 层的接口规范
  - 补全任务状态持久化（写入文件/DB）

- [ ] **日志与监控**
  - 统一日志格式，接入监控/告警

- [ ] **配置管理**
  - 提取硬编码配置（重试次数、写作风格等）到配置文件

- [ ] **单元测试**
  - 为各 Skill 编写单元测试，使用 mock 替代外部依赖

---

## 依赖待安装

```
python-pptx   # PPT 解析
PyPDF2        # PDF 解析（或 pdfminer.six）
python-docx   # DOCX 解析
```
