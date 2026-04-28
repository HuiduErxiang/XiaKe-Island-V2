# Research: 输入结构化 Skill

## 1. PDF 文本提取

**Decision**: PyMuPDF (fitz)

**Rationale**: 同时满足三个需求——文本提取、嵌入图片提取、逐页操作。性能远优于 pdfplumber（纯 Python），且支持增量处理大文件。pdfplumber 强在表格提取但速度慢，pypdf 能力有限。

**Alternatives considered**:
- pdfplumber: 表格提取强，但速度慢（需逐页渲染），不支持图片提取
- pypdf: 轻量但功能不足，无表格/图片提取
- pdfminer.six: 底层库，API 复杂

## 2. OCR 引擎

**Decision**: PaddleOCR

**Rationale**: 医学文献以中文为主，PaddleOCR 中文识别率业界最高（>97%），支持表格识别和版面分析，与扫描件场景高度匹配。

**Alternatives considered**:
- Tesseract + pytesseract: 中文准确率偏低，复杂排版表现差
- EasyOCR: 多语言支持好但中文不如 PaddleOCR，速度更慢
- Surya: 新兴引擎，社区和文档不如 PaddleOCR 成熟

**Dependency**: `paddlepaddle` + `paddleocr`，首次加载需下载中文模型。

## 3. 图表提取与保存

**Decision**: PyMuPDF 提取 PDF 嵌入图片 → Pillow 转换为 PNG；python-pptx 直接从 ZIP 提取 PPTX 图片；python-docx 从 ZIP 提取 DOCX 图片

**Rationale**: PDF/PPTX/DOCX 本质上都是容器格式。PyMuPDF 可提取 PDF 内嵌图片流并定位页码；PPTX/DOCX 是 ZIP 包，图片在 `ppt/media/` 或 `word/media/` 直接可读。

**Naming**: `{源文件名}_p{页码}_fig{序号}.png`

**Constraints**: 
- 矢量图（SVG/EMF）在 PPTX/DOCX 中常见，需 cairosvg 或 Pillow 渲染为 PNG
- 提取图片可能包含重复（如 PDF 页缩略图），需按尺寸过滤（跳过 <100px 图片）

## 4. PPT 解析

**Decision**: python-pptx

**Rationale**: 专为 .pptx 设计，提取幻灯片文本/备注/图片路径简单直接。无替代选择。

**Note**: 不支持 .ppt（旧版格式），按 spec 假定预转换。

## 5. DOCX 解析

**Decision**: python-docx

**Rationale**: 标准 DOCX 库，段落/标题/表格/图片提取均可。

**Note**: 不支持 .doc（旧版格式），按 spec 假定预转换。

## 6. TXT 解析

**Decision**: 纯 Python 内置，无第三方依赖

**Rationale**: 按空行分段逻辑简单，编码检测用 `chardet` 兜底 UTF-8。

## 7. 输出架构

**Decision**: 文件系统输出（`output_dir/` 包含 `structured_input.md` + `assets/`）

**Rationale**: 
- Skill 是同步调用，不涉及网络通信
- 文件系统输出便于下游 Agent 直接读取，无需序列化反序列化
- 图片用相对路径，整体目录可拷贝可归档

## 8. 错误隔离

**Decision**: per-file try/except，失败文件记录 ParseError 但不中断

**Rationale**: 符合 spec FR-008。单文件崩溃不应影响其他文件。

## 9. 测试策略

**Decision**: pytest + 测试 fixtures（准备各类格式样本文件）

**Rationale**: 
- 项目其他 skill 使用 pytest（pdf_distiller 有 tests/）
- 需要真实样本文件（PDF/PPTX/DOCX/TXT/scanned-PDF）作为 fixtures
- 按 spec 的 Acceptance Scenarios 编写测试用例

## 10. 项目结构

**Decision**: 遵循现有 skill 模式（参考 cang_tag_search、pdf_distiller）

```text
.claude/skills/input-structure/
├── SKILL.md              # 技能说明文档
├── main.py               # 入口函数 structure()
├── config.py             # 配置（PaddleOCR 参数、超时等）
├── schema.py             # 数据类定义（StructuredInput, ParsedMaterial 等）
├── parsers/
│   ├── __init__.py
│   ├── pdf_parser.py     # PDF 解析（文本 + OCR + 图片提取）
│   ├── pptx_parser.py    # PPTX 解析
│   ├── docx_parser.py    # DOCX 解析
│   └── txt_parser.py     # TXT 解析
├── utils/
│   ├── __init__.py
│   ├── ocr.py            # PaddleOCR 封装
│   ├── image_extract.py  # 图片提取与保存
│   └── markdown_builder.py # Markdown 组装
├── requirements.txt      # paddleocr, pymupdf, python-pptx, python-docx, pillow, chardet
└── test/
    ├── fixtures/         # 测试样本文件
    ├── test_pdf.py
    ├── test_pptx.py
    ├── test_docx.py
    ├── test_txt.py
    └── test_integration.py
```
