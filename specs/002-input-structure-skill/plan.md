# Implementation Plan: 输入结构化 Skill

**Branch**: `002-input-structure-skill` | **Date**: 2026-04-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-input-structure-skill/spec.md`

## Summary

构建一个 Claude Skill（`input-structure`），将用户提供的 PDF/PPTX/DOCX/TXT 补充材料转换为结构化 Markdown。支持扫描件 OCR、表格转 Markdown table、图表原图提取保存。纯格式转换，不做语义理解。供产品 Agent 在 Speckit 流程 Step ① (specify) 之前调用。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PyMuPDF, PaddleOCR, python-pptx, python-docx, Pillow, chardet
**Storage**: File system (output Markdown + assets/)
**Testing**: pytest
**Target Platform**: Linux server
**Project Type**: Claude Skill (Python library with importable entry point)
**Performance Goals**: Text PDF ≤5s/10pp, Scanned PDF ≤60s/10pp, PPTX ≤3s/20slides
**Constraints**: Single-file failure must not block others, output must be valid Markdown
**Scale/Scope**: 4 format parsers, 3 output entities, ~12 FRs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I - Protected Master Branch
- [x] Feature branch `002-input-structure-skill` created from `master`
- [x] Branch naming follows `feature/xxx-描述` convention

### Principle II - Feature Branch Workflow
- [x] Plan documents the target branch for implementation
- [x] No direct commits to `master` anticipated in this plan

### Principle III - Dual Environment Deployment
- [x] Skill is a Python library, deployed via file copy to `.claude/skills/`, no port conflicts
- [x] Development: test locally with `pytest` and `PYTHONPATH`

### Principle IV - Deployment Gatekeeping
- [x] Skill deployment is file-based (copy to `.claude/skills/input-structure/`), no `deploy.sh` needed
- [x] Working directory state tracked by git

### Principle V - Minimum Invasive Changes
- [x] New dependency `paddleocr` is justified (Chinese OCR requirement, no existing OCR in project)
- [x] New dependency `pymupdf` is justified (best PDF text+image extraction, replacing no existing PDF lib)
- [x] No database schema changes (file-based output only)
- [x] Follows existing skill pattern (reference: `cang_tag_search`, `pdf_distiller`)

**Complexity Tracking**: No violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-input-structure-skill/
├── plan.md              # This file
├── research.md          # Phase 0: Technical decisions
├── data-model.md        # Phase 1: Entities and data structures
├── quickstart.md        # Phase 1: Quick start guide
├── contracts/           # Phase 1: Public API contract
│   └── skill-api.md
└── tasks.md             # Phase 2: /speckit.tasks output (NOT created by /speckit.plan)
```

### Source Code (repository root: `.claude/skills/input-structure/`)

```text
.claude/skills/input-structure/
├── SKILL.md              # Skill description (for Claude discovery)
├── __init__.py           # Package init, exports structure()
├── main.py               # Entry point: structure(input_text, file_paths, output_dir, ...)
├── config.py             # PaddleOCR params, timeouts, size limits
├── schema.py             # Dataclasses: StructuredInput, ParsedMaterial, ParsedImage, ParseError
├── parsers/
│   ├── __init__.py
│   ├── pdf_parser.py     # PDF → ParsedMaterial (PyMuPDF text + PaddleOCR fallback + image extract)
│   ├── pptx_parser.py    # PPTX → ParsedMaterial (python-pptx)
│   ├── docx_parser.py    # DOCX → ParsedMaterial (python-docx)
│   └── txt_parser.py     # TXT → ParsedMaterial (built-in + chardet)
├── utils/
│   ├── __init__.py
│   ├── ocr.py            # PaddleOCR wrapper (init, recognize_page, confidence check)
│   ├── image_extract.py  # Image extraction (PyMuPDF for PDF, ZIP for PPTX/DOCX)
│   └── markdown_builder.py  # Assemble final Markdown from ParsedMaterial list
├── requirements.txt      # pymupdf, paddleocr, paddlepaddle, python-pptx, python-docx, pillow, chardet
└── test/
    ├── fixtures/         # Sample files: text-pdf, scanned-pdf, pptx, docx, txt, mixed
    ├── test_pdf_parser.py
    ├── test_pptx_parser.py
    ├── test_docx_parser.py
    ├── test_txt_parser.py
    ├── test_ocr.py
    ├── test_image_extract.py
    ├── test_markdown_builder.py
    └── test_integration.py
```

**Structure Decision**: Single-project structure following existing skill pattern. All source under `.claude/skills/input-structure/`. Test fixtures live alongside tests.

## Implementation Phases

### Phase 0: Foundation (schema + config + requirements)

1. Create `.claude/skills/input-structure/` directory structure
2. Write `requirements.txt`
3. Write `schema.py` — all 4 dataclasses
4. Write `config.py` — OCR params, timeout values, size limits

### Phase 1: Parsers

5. Write `utils/ocr.py` — PaddleOCR init + recognize wrapper
6. Write `utils/image_extract.py` — image extraction from PDF/PPTX/DOCX
7. Write `parsers/pdf_parser.py` — text extraction + OCR fallback + table detection + image extraction
8. Write `parsers/pptx_parser.py` — slide-by-slide with image extraction
9. Write `parsers/docx_parser.py` — heading-preserving with image extraction
10. Write `parsers/txt_parser.py` — paragraph-split with encoding detection

### Phase 2: Assembly

11. Write `utils/markdown_builder.py` — assemble ParsedMaterial[] → final Markdown
12. Write `main.py` — structure() entry point orchestrating all parsers + builder
13. Write `SKILL.md` — skill documentation
14. Write `__init__.py` — package exports

### Phase 3: Testing

15. Prepare test fixtures (sample files for all formats)
16. Write unit tests for each parser
17. Write unit tests for OCR utility
18. Write unit tests for image extraction
19. Write integration tests per spec Acceptance Scenarios
20. Run full test suite, verify coverage ≥80%

## Estimated Complexity

| Module | Lines | Difficulty |
|--------|-------|------------|
| schema.py | ~60 | Low |
| config.py | ~30 | Low |
| utils/ocr.py | ~80 | Medium (PaddleOCR API) |
| utils/image_extract.py | ~120 | Medium (multi-format extraction) |
| utils/markdown_builder.py | ~80 | Low |
| parsers/pdf_parser.py | ~200 | High (text + OCR + tables + images) |
| parsers/pptx_parser.py | ~80 | Low |
| parsers/docx_parser.py | ~80 | Low |
| parsers/txt_parser.py | ~40 | Low |
| main.py | ~80 | Medium (orchestration) |
| SKILL.md | ~60 | Low |
| tests/ | ~400 | Medium |

**Total**: ~1,300 lines of code + tests
