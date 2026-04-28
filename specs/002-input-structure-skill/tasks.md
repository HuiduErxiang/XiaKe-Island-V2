# Tasks: 输入结构化 Skill

**Input**: Design documents from `/specs/002-input-structure-skill/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY per spec Acceptance Scenarios. Target test coverage ≥80%.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Different files, no dependencies — can run in parallel
- **[Story]**: Maps task to user story (US1, US2, US3)
- All paths relative to `/root/huidu/.claude/skills/input-structure/`

---

## Phase 1: Setup

**Purpose**: Project scaffolding — directory structure and dependencies

- [x] T001 Create directory structure: `.claude/skills/input-structure/{parsers,utils,test/fixtures}`
- [x] T002 Write `requirements.txt` — pymupdf, paddlepaddle, paddleocr, python-pptx, python-docx, pillow, chardet

**Checkpoint**: Virtual env installs cleanly with `pip install -r requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and config — MUST complete before ANY user story

**⚠️ CRITICAL**: No parser work can begin until this phase is complete

- [x] T003 [P] Write `.claude/skills/input-structure/schema.py` — all 4 dataclasses (StructuredInput, ParsedMaterial, ParsedImage, ParseError) per data-model.md
- [x] T004 [P] Write `.claude/skills/input-structure/config.py` — OCR params, timeout values (30s/page), size limits (50MB), image min dimensions (100px)
- [x] T005 Write `.claude/skills/input-structure/__init__.py` — package init, re-export `structure` from main

**Checkpoint**: `from input_structure import structure` imports without error (function not yet defined, placeholder OK)

---

## Phase 3: User Story 1 — PDF 解析 (Priority: P1) 🎯 MVP

**Goal**: PDF → structured Markdown with OCR fallback, table conversion, and chart extraction

**Independent Test**: Provide a 5-page text PDF + "写一篇关于仑卡奈单抗的科普文章", Skill returns Markdown with user request + per-page content

### Tests for User Story 1 ⚠️

> **Write these FIRST, ensure they FAIL before implementation**

- [x] T006 [P] [US1] Prepare test fixtures for PDF tests in `.claude/skills/input-structure/test/fixtures/` — text-layer PDF (3pp), scanned PDF (2pp), PDF with tables (2pp), PDF with charts (2pp)
- [x] T007 [P] [US1] Write `.claude/skills/input-structure/test/test_ocr.py` — test PaddleOCR init, recognize_page, confidence threshold, timeout
- [x] T008 [P] [US1] Write `.claude/skills/input-structure/test/test_image_extract.py` — test image extraction from PDF (embedded images), naming convention, min-size filter
- [x] T009 [P] [US1] Write `.claude/skills/input-structure/test/test_pdf_parser.py` — per spec Acceptance Scenarios: text extraction, title hierarchy preservation, scanned page OCR annotation `[第X页 — OCR 识别]`, table → Markdown table, chart → `![图题](./assets/...)`

### Implementation for User Story 1

- [x] T010 [US1] Implement `.claude/skills/input-structure/utils/ocr.py` — PaddleOCR init, `recognize_page(image_path) -> str`, confidence check, timeout guard (depends on T007 tests existing)
- [x] T011 [US1] Implement `.claude/skills/input-structure/utils/image_extract.py` — `extract_images_from_pdf(page, output_dir, filename) -> list[ParsedImage]`, min-size filter, PNG save (depends on T008 tests existing)
- [x] T012 [US1] Implement `.claude/skills/input-structure/parsers/pdf_parser.py` — `parse_pdf(path) -> ParsedMaterial`: PyMuPDF text extraction with title detection, PaddleOCR fallback for pages with no text, table detection + Markdown table conversion, chart extraction via image_extract, error isolation per page (depends on T003, T004, T010, T011)

**Checkpoint**: `parse_pdf("text_pdf")` returns valid ParsedMaterial; `parse_pdf("scanned_pdf")` returns OCR-annotated ParsedMaterial; all T009 tests pass

---

## Phase 4: User Story 2 — PPTX/DOCX/TXT 解析 (Priority: P2)

**Goal**: PPTX/DOCX/TXT → structured Markdown, preserving hierarchy and formatting

**Independent Test**: 10-slide PPTX returns Markdown with `### Slide N — 标题` + text + notes

### Tests for User Story 2 ⚠️

- [x] T013 [P] [US2] Prepare test fixtures in `.claude/skills/input-structure/test/fixtures/` — PPTX (5 slides with notes), DOCX (multi-level headings), TXT (paragraphs, UTF-8), TXT (GBK encoding)
- [x] T014 [P] [US2] Write `.claude/skills/input-structure/test/test_pptx_parser.py` — per spec: slide title + body + notes, slide numbering, image extraction with alt text, multi-format mixed input ordering
- [x] T015 [P] [US2] Write `.claude/skills/input-structure/test/test_docx_parser.py` — per spec: heading hierarchy (H1/2/3 → #/##/###), paragraph preservation, image extraction
- [x] T016 [P] [US2] Write `.claude/skills/input-structure/test/test_txt_parser.py` — per spec: paragraph split on blank lines, no-blank-line raw passthrough, UTF-8/GBK encoding, empty file (0 bytes)

### Implementation for User Story 2

- [x] T017 [P] [US2] Implement `.claude/skills/input-structure/parsers/pptx_parser.py` — `parse_pptx(path) -> ParsedMaterial`: per-slide extraction (title, body, notes), image extraction from `ppt/media/`, alt text as caption (depends on T003, T004)
- [x] T018 [P] [US2] Implement `.claude/skills/input-structure/parsers/docx_parser.py` — `parse_docx(path) -> ParsedMaterial`: heading-preserving extraction (Heading 1/2/3 → #/##/###), paragraph extraction, image extraction from `word/media/` (depends on T003, T004)
- [x] T019 [P] [US2] Implement `.claude/skills/input-structure/parsers/txt_parser.py` — `parse_txt(path) -> ParsedMaterial`: UTF-8 read with chardet fallback, paragraph split on `\n\n`, raw passthrough when no blank lines (depends on T003, T004)

**Checkpoint**: All three parsers return valid ParsedMaterial; T014, T015, T016 tests pass

---

## Phase 5: Assembly, US3 Passthrough & Integration

**Goal**: Wire parsers together behind `structure()` entry point; handle no-file case (US3); full integration tests

### Tests

- [x] T020 [P] [US3] Write `.claude/skills/input-structure/test/test_passthrough.py` — per spec: no-file returns only user request + 「补充材料」=「无」; empty file (0 bytes) annotation; unsupported format skip
- [x] T021 Write `.claude/skills/input-structure/test/test_integration.py` — end-to-end per spec Acceptance Scenarios: mixed PDF+PPTX+DOCX ordering, single failure doesn't block others, ≥50 chart images only inline first 20, full roundtrip `structure()` call

### Implementation

- [x] T022 Implement `.claude/skills/input-structure/utils/markdown_builder.py` — `build_markdown(materials: list[ParsedMaterial], user_request: str, assets_dir: str) -> str`: assemble final Markdown per data-model.md template, inline first 20 images only when count >50 (depends on T003)
- [x] T023 Implement `.claude/skills/input-structure/main.py` — `structure(input_text, file_paths, output_dir, ocr_enabled, ocr_timeout) -> StructuredInput`: route each file to correct parser by extension, collect results, handle US3 passthrough (empty file_paths → materials=[]), call markdown_builder, write structured_input.md + save assets, return StructuredInput (depends on T012, T017, T018, T019, T022)
- [x] T024 Implement `.claude/skills/input-structure/SKILL.md` — skill documentation per existing pattern (cang_tag_search/SKILL.md format): description, usage examples, supported formats, error handling notes

**Checkpoint**: `structure("写文章", ["a.pdf", "b.pptx", "c.txt"], "/tmp/out/")` produces valid output; all T020, T021 tests pass

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, coverage, and quality gates

- [x] T025 Run full test suite with `pytest test/ -v --cov=. --cov-report=term`, verify ≥80% line coverage. Run timing assertions: per SC-001 (text PDF ≤5s), SC-001a (scanned PDF ≤60s), SC-002 (PPTX ≤3s).
- [x] T026 [P] Verify quickstart.md examples execute successfully against the implemented skill
- [x] T027 [P] Edge case sweep: unsupported format, encrypted PDF, file >50MB, corrupted image, complex merged cells table, duplicate file dedup — verify each produces expected error annotation per spec Edge Cases. Include FR-009 verification: assert output contains no AI-generated summaries, opinions, or synthesized conclusions (output must be purely extracted + formatted content)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Setup (Phase 1)
    ↓
Foundational (Phase 2) ← BLOCKS ALL user stories
    ↓
    ├── US1: PDF (Phase 3) 🎯 MVP
    ├── US2: PPTX/DOCX/TXT (Phase 4) ← can start after Foundational
    └── US3: Passthrough + Assembly (Phase 5) ← depends on US1 + US2 parsers
          ↓
      Polish (Phase 6)
```

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational. No dependency on US2/US3.
- **US2 (P2)**: Independent after Foundational. Can run parallel with US1.
- **US3 (P3)**: Depends on US1 + US2 parsers being complete (main.py orchestrates them all).

### Within User Story 1

```
T006, T007, T008, T009 (tests) → can all run in parallel
    ↓
T010 (ocr.py) → T011 (image_extract.py) → T012 (pdf_parser.py)
```

T010 and T011 are parallel (different files).

### Parallel Opportunities

- **Phase 2**: T003, T004 are parallel (different files)
- **Phase 3 tests**: T006, T007, T008, T009 all parallel
- **Phase 3 impl**: T010 ∥ T011, then T012
- **Phase 4**: T013-T016 tests all parallel; T017 ∥ T018 ∥ T019 implementation
- **Phase 5**: T020 ∥ T022 (test ∥ markdown_builder)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1: PDF)
                                                ↓
                                         STOP & VALIDATE
```

After Phase 3, you have a working PDF → Markdown converter with OCR. Can deploy/demo immediately.

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1: PDF → Deploy/Demo (MVP!) — handles the most common format
3. US2: PPTX/DOCX/TXT → Deploy/Demo — full format coverage
4. US3 + Assembly → Deploy/Demo — end-to-end with Product Agent integration
5. Polish → Production ready

### Commit Points

- After Phase 2: `feat: add input-structure schema and config`
- After Phase 3: `feat: add PDF parser with OCR support`
- After Phase 4: `feat: add PPTX/DOCX/TXT parsers`
- After Phase 5: `feat: add structure() entry point and integration`
- After Phase 6: `chore: polish, coverage, edge cases`

---

## Summary

| Metric | Count |
|--------|-------|
| Total tasks | 27 |
| US1 tasks | 7 (T006–T012) |
| US2 tasks | 7 (T013–T019) |
| US3 tasks | 3 (T020, T023, part of T023) |
| Setup/Foundational | 5 (T001–T005) |
| Assembly/Integration | 3 (T021, T022, T024) |
| Polish | 3 (T025–T027) |
| Parallel opportunities | 14 tasks marked [P] |
| MVP scope (US1 only) | T001–T012 (12 tasks) |
