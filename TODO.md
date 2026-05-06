# TODO - AI 写作系统待办事项

> 最后更新：2026-05-06（003-product-review-skill 完成）

## 整体进度 ~33%

| Phase | 完成度 | 状态 |
|-------|--------|------|
| Phase 1 · 数据来源层 | 60% (3/5) | 缺 TagSimplifier、KVIndexBuilder |
| Phase 2 · 产品 Agent | 66% (2/3) | 缺证据补充 Skill（👤 同事） |
| Phase 3 · 写作 Agent | 0% | — |
| Phase 4 · 工程化 | 10% | — |

---

## Phase 1 · 数据来源层

- [x] **cang_tag_search Skill** `.claude/skills/cang_tag_search/`
  - 22/22 测试通过，生产库试运行正常（62 tags, 309 materials, 745 relations）

- [ ] **标签简化模块** — TagSimplifier
  - 对素材平台 tags 表进行清洗（去噪、去重、规范化命名）

- [ ] **KV 索引构建** — KVIndexBuilder
  - 确定存储方案（内存 / Redis / 本地 JSON）

- [ ] **标签检索** — TagRetriever
  - 意图 → 标签匹配算法（关键词匹配 / 向量检索）

- [ ] **证据提取 Skill** 👤 同事负责
  - 根据检索结果定位 uploads 目录下的 PDF 文件
  - 从 PDF 中精细抽取结构化证据片段

---

## Phase 2 · 产品 Agent

- [x] **input_structure Skill** `.claude/skills/input_structure/`
  - 36/36 测试通过，支持 PDF/PPTX/DOCX/TXT → Markdown

- [x] **product-review Skill** `.claude/skills/product-review/`
  - 36/36 测试通过，支持证据审核 + PRD 审核双模式
  - Mock 实现（规则匹配），同事可替换 `reviewer.py` 内部逻辑

- [ ] **证据补充 Skill** 👤 同事负责
  - 从 PRD 内容中提取检索意图
  - 调用素材平台数据库查询注入证据到 PRD

- [ ] **产品 Agent 编排器**
  - 编排 input_structure → cang_tag_search → 证据提取 → 证据审核 → 补充循环 → PRD 撰写 → PRD 审核 → 人类确认
  - 管理人类确认节点的交互逻辑
  - 管理补充循环（证据不足时触发）

- [ ] **PRD 撰写 Skill**
  - 基于结构化写作需求和审核通过的证据生成 PRD 草稿

---

## Phase 3 · 写作 Agent

- [ ] **写作 Skills**
  - 确定写作 Skill 列表（Speckit 技能组）
  - 实现多风格/类型写作（informational / narrative / persuasive）

- [ ] **写作审核子 Agent**
  - 审核维度：可读性 / 准确性 / 风格一致性
  - 审核后回写修改意见，触发迭代修正

---

## Phase 4 · 工程化

- [ ] **Orchestrator 通信管理**
  - 数据层 ↔ 执行 Agent 层的接口规范
  - 任务状态持久化

- [ ] **日志与监控**
- [ ] **配置管理** — 提取硬编码配置到配置文件
- [ ] **单元测试覆盖** — 为编排器和未测试模块补测试

---

## 依赖

```
pydantic>=2.0.0  # product-review（已在 cang_tag_search 中引入）
python-pptx      # input_structure
PyPDF2           # input_structure
python-docx      # input_structure
```

---

## 下一步

1. **产品 Agent 编排器** — 把已有的 3 个 Skill（input_structure、cang_tag_search、product-review）串联成 Pipeline
2. **PRD 撰写 Skill** — 补齐 PRD 生成能力，打通「输入 → 审核 → 交付」全流程
