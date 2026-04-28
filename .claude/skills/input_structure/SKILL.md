---
name: input-structure
description: 将用户提供的 PDF/PPTX/DOCX/TXT 补充材料转换为结构化 Markdown，供下游 Agent 消费。纯格式转换，不做意图理解、不做证据归类。
---

# 输入结构化 Skill

将 PDF/PPTX/DOCX/TXT 补充材料转换为结构化 Markdown，供产品 Agent 在 Speckit 流程 Step ① (specify) 之前调用。

## 功能

- **PDF 解析**：逐页提取文本，保留标题层级；扫描件自动启用 PaddleOCR
- **表格转换**：PDF 中的表格自动转 Markdown table
- **图表提取**：图表原图保存为 PNG，Markdown 中相对路径引用
- **PPTX/DOCX/TXT**：支持幻灯片、文档、纯文本的统一结构化
- **错误隔离**：单文件失败不阻塞其他文件

## 使用方式

```python
from input_structure import structure

result = structure(
    input_text="写一篇关于仑卡奈单抗的科普文章",
    file_paths=["/data/clinical_trial.pdf"],
    output_dir="/tmp/structured_output/"
)

# 输出文件：
# /tmp/structured_output/structured_input.md
# /tmp/structured_output/assets/*.png
```

## 支持格式

| 格式 | 扩展名 | 解析方式 |
|------|--------|---------|
| PDF (文本层) | `.pdf` | PyMuPDF 文本提取 |
| PDF (扫描件) | `.pdf` | PaddleOCR |
| PowerPoint | `.pptx` | python-pptx |
| Word | `.docx` | python-docx |
| Plain Text | `.txt` | 内置 + chardet 编码检测 |

## 不做

- ❌ 意图理解/分类
- ❌ 证据归类/摘要
- ❌ 关键论点提取
- ❌ 任何形式的语义分析
