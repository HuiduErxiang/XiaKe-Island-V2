# 产品审核子 Agent Skill

对产品 Agent Pipeline 中的证据和 PRD 草稿进行结构化审核。支持两种模式：

- **证据审核** (`evidence_review`): 判断写作需求的证据覆盖是否充分，输出充分性判定和补充建议
- **PRD 审核** (`prd_review`): 审核 PRD 草稿的逻辑贯通性、论证质量、合规性，输出通过/返修判定和改写目标

当前为 **Mock 实现**：真实 Pydantic schema + 基于规则的关键词匹配。同事后续替换 `reviewer.py` 内部实现即可升级。

## 入口

```python
from product_review import review

result = review(
    mode="evidence_review",
    writing_requirement="## 写作需求\n...",
    evidence_fragments=[{"content": "...", "source": "..."}],
)
```

## 接口契约

输入输出 schema 定义在 `schema.py`，为不可修改的接口契约。`reviewer.py` 可由同事替换内部实现。

完整 API 文档见 `specs/003-product-review-skill/contracts/skill-api.md`。
