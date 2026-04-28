# Data Model: 输入结构化 Skill

## Entity Diagram

```
StructuredInput (1) ──< (N) ParsedMaterial
                               │
                               ├── (0..N) ParsedImage
                               └── (0..1) ParseError
```

## Entities

### StructuredInput

Skill 顶层输出，代表一次结构化处理的结果。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_request` | `str` | ✓ | 用户原始写作需求文本 |
| `materials` | `list[ParsedMaterial]` | ✓ | 有序的补充材料列表 |
| `assets_dir` | `str` | | 图片资源目录路径（无图片时为空） |
| `parsed_at` | `datetime` | ✓ | 解析完成时间戳 |

**Validation**:
- `user_request` 不可为空字符串
- `materials` 为空列表时，输出仅含「用户写作需求」章节

### ParsedMaterial

单个文件的解析结果。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `filename` | `str` | ✓ | 原始文件名 |
| `format` | `enum` | ✓ | pdf / pptx / docx / txt |
| `content` | `str` | ✓ | 结构化 Markdown 文本 |
| `page_count` | `int` | | 页码（PDF）/ 幻灯片数（PPTX）/ 段落数（DOCX/TXT） |
| `images` | `list[ParsedImage]` | | 提取的图表图片 |
| `error` | `ParseError` | | 解析失败时填充 |

**State transitions**: none (immutable result object)

### ParsedImage

从文档中提取的图表/图片。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_file` | `str` | ✓ | 所属源文件名 |
| `page` | `int` | ✓ | 所在页码（PDF）/ 幻灯片序号（PPTX） |
| `index` | `int` | ✓ | 页内图片序号（从 1 开始） |
| `caption` | `str` | | 图题文本（PDF caption / PPT alt text） |
| `path` | `str` | ✓ | 保存路径 `assets/{file}_p{page}_fig{index}.png` |
| `width` | `int` | | 图片宽度（px） |
| `height` | `int` | | 图片高度（px） |

**Validation**:
- `path` 必须为 `assets/` 下的相对路径
- 小图片（<100px 宽高）自动跳过，不纳入此列表

### ParseError

单个文件解析失败时的错误记录。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `filename` | `str` | ✓ | 失败的文件名 |
| `reason` | `str` | ✓ | 失败原因描述 |
| `blocks_others` | `bool` | ✓ | 是否阻塞其他文件（始终为 `false`） |

### Error Reason Enum

标准化失败原因字符串：

| 原因 | 触发条件 |
|------|---------|
| `unsupported_format` | .xlsx, .jpg, .mp4 等非支持格式 |
| `file_not_found` | 路径不存在或不可读 |
| `encrypted_pdf` | PDF 有密码保护 |
| `file_too_large` | 文件 >50MB |
| `empty_file` | 0 字节文件 |
| `ocr_timeout` | 单页 OCR 超过 30s |
| `corrupted_image` | 图表原图损坏无法提取 |
| `parse_error` | 其他解析异常 |

## Output File Structure

```
{output_dir}/
├── structured_input.md
└── assets/
    ├── report_p3_fig1.png
    ├── report_p5_fig2.png
    └── slides_slide2_img1.png
```

## Markdown Output Template

```markdown
# 用户写作需求

{user_request}

---

# 补充材料

## {filename_1}

### 第1页

{content...}

### 第2页

{content...}

![图1: 疗效对比](./assets/file1_p2_fig1.png)

---

## {filename_2}

{content...}
```
