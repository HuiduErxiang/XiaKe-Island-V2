# Quickstart: 输入结构化 Skill

## 安装依赖

```bash
cd /root/huidu/.claude/skills/input-structure
pip install -r requirements.txt
```

## 快速使用

### 1. 纯文本（无文件）

```python
import asyncio
from input_structure import structure

result = structure(
    input_text="写一篇关于仑卡奈单抗的科普文章",
    file_paths=[],
    output_dir="/tmp/structured_output/"
)
# → structured_input.md 仅含「用户写作需求」章节
```

### 2. 解析 PDF

```python
result = structure(
    input_text="写一篇关于阿尔茨海默病的综述",
    file_paths=["/data/chengongzi_clinical_trial.pdf"],
    output_dir="/tmp/structured_output/"
)
# → structured_input.md 含用户需求 + PDF 逐页内容
# → 如 PDF 有表格，自动转 Markdown table
# → 图表保存到 assets/，Markdown 中 ![]() 引用
```

### 3. 解析扫描件 PDF

```python
result = structure(
    input_text="分析这份临床报告",
    file_paths=["/data/scanned_report.pdf"],
    output_dir="/tmp/structured_output/",
    ocr_enabled=True,
    ocr_timeout=30
)
# 页面标注 `[第X页 — OCR 识别]`
```

### 4. 混合格式

```python
result = structure(
    input_text="综合分析以下材料",
    file_paths=[
        "/data/paper.pdf",
        "/data/presentation.pptx",
        "/data/notes.txt"
    ],
    output_dir="/tmp/structured_output/"
)
# 按输入顺序组织输出，互不干扰
```

### 5. 查看输出

```bash
cat /tmp/structured_output/structured_input.md
ls /tmp/structured_output/assets/
```

## 输出示例

```markdown
# 用户写作需求

写一篇关于仑卡奈单抗的科普文章

---

# 补充材料

## chengongzi_clinical_trial.pdf

### 第1页

# 一项仑卡奈单抗治疗早期阿尔茨海默病的III期临床试验

**作者**: van Dyck CH, Swanson CJ, Aisen P, et al.
**来源**: New England Journal of Medicine, 2023

### 第2页

| 指标 | 仑卡奈单抗组 (n=898) | 安慰剂组 (n=897) | p值 |
|------|---------------------|------------------|-----|
| CDR-SB 变化 | 1.21 | 1.66 | <0.001 |
| 淀粉样蛋白负担 | -55.48 | 3.64 | <0.001 |

![图1: CDR-SB 评分随时间变化](./assets/chengongzi_clinical_trial_p2_fig1.png)

*图题: CDR-SB 评分随时间变化*

### 第3页 — OCR 识别

讨论...
```
