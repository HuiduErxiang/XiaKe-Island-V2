# Quick Start: 003-product-review-skill

## 安装

```bash
cd /root/huidu/.claude/skills/product-review
pip install -r requirements.txt  # pydantic (仅依赖)
```

## 基本用法

### 1. 证据审核

```python
from product_review import review

result = review(
    mode="evidence_review",
    writing_requirement="""
## 写作需求
写一篇关于仑卡奈单抗（lecanemab）治疗阿尔茨海默病的科普文章。

### 需要覆盖的信息点
- 疗效数据：III 期临床试验主要终点
- 安全性数据：ARIA 发生率
- 作用机制：Aβ 原纤维靶向
""",
    evidence_fragments=[
        {
            "content": "Clarity AD 试验：仑卡奈单抗组 CDR-SB 评分较基线变化 -0.45，安慰剂组 -0.18（p<0.001）",
            "source": "NEJM 2023; 388:9-21",
            "theme": "疗效数据"
        },
        {
            "content": "仑卡奈单抗靶向可溶性 Aβ 原纤维，减少淀粉样蛋白斑块沉积",
            "source": "文献综述",
            "theme": "作用机制"
        }
    ]
)

print(result["sufficiency"])       # "partial"
print(result["ready_for_drafting"]) # False
for hint in result["supplement_hints"]:
    print(f"[{hint['priority']}] {hint['description']}")
# [high] 建议补充 III 期临床试验的安全性数据，重点关注 ARIA-E 和 ARIA-H 发生率
```

### 2. PRD 审核

```python
result = review(
    mode="prd_review",
    writing_requirement="## 写作需求\n...",
    prd_content="""
## PRD 草案

### 疗效分析
仑卡奈单抗在 III 期试验中显著减缓认知下降（CDR-SB -0.45 vs -0.18）。

### 安全性分析
仑卡奈单抗总体安全可控。
"""
)

print(result["verdict"])           # "revision_required"
for rt in result["rewrite_targets"]:
    print(f"[{rt['severity']}] {rt['section']}: {rt['issue']}")
# [high] 安全性分析: 该章节结论缺乏证据支撑
```

## CLI 测试

```bash
cd /root/huidu/.claude/skills/product-review

# 证据审核
python main.py review \
  --mode evidence_review \
  --requirement "写作需求文本..." \
  --evidence '[{"content":"证据1","source":"来源1"}]'

# PRD 审核
python main.py review \
  --mode prd_review \
  --requirement "写作需求文本..." \
  --prd "PRD 草稿内容..."
```

## Pipeline 集成

编排器调用顺序（产品 Agent 内部）：

```python
# Step 1: 结构化输入
from input_structure import structure
structured = structure(input_text=user_requirement, file_paths=[...])

# Step 2: 标签检索
from cang_tag_search import search
assets = await search(tags=["阿尔茨海默病", "仑卡奈单抗"])

# Step 3: 证据提取（👤 同事负责）
evidence = colleague_extract(assets, structured)

# Step 4: 证据审核（本 Skill — 证据模式）
from product_review import review
evidence_result = review(
    mode="evidence_review",
    writing_requirement=structured["markdown"],
    evidence_fragments=evidence
)

if not evidence_result["ready_for_drafting"]:
    # → 进入补充循环（编排器负责）
    pass

# Step 5: PRD 撰写（后续 Skill）
prd = draft_prd(structured, evidence)

# Step 6: PRD 审核（本 Skill — PRD 模式）
prd_result = review(
    mode="prd_review",
    writing_requirement=structured["markdown"],
    prd_content=prd
)

if prd_result["ready_for_handoff"]:
    # → 交付写作 Agent（Phase 3）
    pass
```
