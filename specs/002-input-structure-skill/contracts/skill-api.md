# Skill API Contract: input-structure

## Entry Point

```python
from input_structure import structure

result = structure(
    input_text="用户写作需求描述",
    file_paths=["/path/to/doc1.pdf", "/path/to/doc2.pptx"],
    output_dir="/path/to/output/"
)
```

## Parameters

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `input_text` | `str` | ✓ | | 用户原始写作需求文本 |
| `file_paths` | `list[str]` | ✓ | | 文件路径列表，可为空列表 `[]` |
| `output_dir` | `str` | ✓ | | 输出目录（Skill 会在其下创建 `structured_input.md` 和 `assets/`） |
| `ocr_enabled` | `bool` | | `True` | 是否启用 OCR 处理扫描件 |
| `ocr_timeout` | `int` | | `30` | 单页 OCR 超时（秒） |

## Return Value

```python
StructuredInput(
    user_request: str,
    materials: list[ParsedMaterial],
    assets_dir: str | None,
    parsed_at: datetime
)
```

## Output Files

```
{output_dir}/
├── structured_input.md    # 主输出 Markdown
└── assets/                # 提取的图表图片（可能为空）
    └── *.png
```

## Error Handling

- 不抛异常。所有解析失败记录在 `ParsedMaterial.error` 中
- 单个文件失败不阻塞其他文件
- 无文件时 `materials=[]`，输出仅含用户需求章节

## Calling Convention (Product Agent)

产品 Agent 在 Step ① (specify) 之前调用：

```python
# Spawn input-structure skill, wait for result
result = structure(
    input_text=user_raw_input,
    file_paths=uploaded_files,
    output_dir="/tmp/structured_input/"
)

# Pass result markdown to speckit.specify
spec_markdown = f"{result.user_request}\n\n---\n\n{chr(10).join(m.content for m in result.materials)}"
```

## Supported Formats

| 格式 | 扩展名 | 解析方式 |
|------|--------|---------|
| PDF (text layer) | `.pdf` | PyMuPDF 文本提取 |
| PDF (scanned) | `.pdf` | PaddleOCR |
| PowerPoint | `.pptx` | python-pptx |
| Word | `.docx` | python-docx |
| Plain Text | `.txt` | 内置 open() |
