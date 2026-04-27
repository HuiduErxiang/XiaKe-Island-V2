# Tasks: 藏经阁标签检索 Skill

**Input**: Design documents from `/specs/001-cang-tag-search-skill/`
**Prerequisites**: plan.md (done), spec.md (done), research.md (done), data-model.md (done), contracts/ (done)

**Status Note**: Phase 1 (Setup & Gap Fixes) was completed during the `/speckit.plan` session. DB path corrected, `__init__.py` added, `requirements.txt` added, SKILL.md files updated, directory renamed `cang-tag-search` → `cang_tag_search`. The remaining work is tests and integration validation.

---

## Phase 1: Setup & Gap Fixes ✅ (COMPLETED)

- [x] T001 Fix `DEFAULT_DB_PATH` in `.kimi/skills/cang_tag_search/config.py` — `database-dev.sqlite` → `database.sqlite`
- [x] T002 [P] Add `__init__.py` in `.kimi/skills/cang_tag_search/__init__.py` — re-export public API (pdf-distiller pattern)
- [x] T003 [P] Add `requirements.txt` in `.kimi/skills/cang_tag_search/requirements.txt` — `pydantic>=2.0`
- [x] T004 [P] Update SKILL.md DB references in `.claude/skills/cang-tag-search/SKILL.md` and `.kimi/skills/cang_tag_search/SKILL.md`
- [x] T005 Rename package directory `.kimi/skills/cang-tag-search/` → `.kimi/skills/cang_tag_search/` (Python requires underscores)

---

## Phase 2: Pytest Infrastructure (Foundational)

**Purpose**: Test framework that all user story tests depend on.

**⚠️ CRITICAL**: No user story tests can run until this phase is complete.

- [ ] T006 Create `tests/` directory and `conftest.py` in `.kimi/skills/cang_tag_search/tests/conftest.py` with fixtures:
  - `db_path`: temp SQLite with test schema
  - `populated_db`: DB seeded with sample tags, categories, materials, material_tags
  - `sample_asset`: a `KnowledgeAsset` instance for evidence extraction tests
  - `config`: `SearchConfig` and `EvidenceConfig` pointing at temp DB
- [ ] T007 [P] Add `pytest`, `pytest-asyncio` to `requirements.txt` in `.kimi/skills/cang_tag_search/requirements.txt`
- [ ] T008 Verify test infrastructure: `cd .kimi/skills/cang_tag_search && pytest --collect-only` shows no errors

**Checkpoint**: Test infrastructure ready — user story tests can now be written.

---

## Phase 3: User Story 1 — 按标签检索知识资产 (Priority: P1) 🎯 MVP

**Goal**: Product Agent 传入标签名，Skill 从素材平台数据库返回匹配的知识资产（PDF 文献），按匹配标签数排序。

**Independent Test**: `search(tags=["仑卡奈单抗"])` 返回匹配的 `KnowledgeAsset` 列表，包含分类和标签信息。

### Tests for User Story 1

- [ ] T009 [P] [US1] Test `search()` returns assets for exact tag match in `tests/test_search.py`
- [ ] T010 [P] [US1] Test `search()` with multiple tags (OR logic, match count sorting) in `tests/test_search.py`
- [ ] T011 [P] [US1] Test `search()` returns empty result for non-matching tags (spec FR-006) in `tests/test_search.py`
- [ ] T012 [P] [US1] Test `search()` respects `max_results` limit in `tests/test_search.py`
- [ ] T013 [P] [US1] Test `search()` handles empty tags list gracefully in `tests/test_search.py`
- [ ] T014 [P] [US1] Test `search()` result contains `total_matches`, `query_tags`, `execution_time_ms` in `tests/test_search.py`

### Implementation for User Story 1

> Implementation already exists in `.kimi/skills/cang_tag_search/main.py` (`search` function). Tasks focus on verification and edge case hardening.

- [ ] T015 [US1] Verify `search()` returns `type='document'` only (no images/videos) in `.kimi/skills/cang_tag_search/main.py`
- [ ] T016 [US1] Verify case-insensitive tag matching works in `.kimi/skills/cang_tag_search/main.py`

**Checkpoint**: User Story 1 fully functional. MVP is searchable.

---

## Phase 4: User Story 2 — 获取完整标签体系 (Priority: P2)

**Goal**: Product Agent 获取素材平台所有可用标签和分类，用于生成精准检索意图。

**Independent Test**: `get_all_tags()` 返回的标签数 >= 数据库 `tags` 表中的记录数，无重复、无遗漏（spec SC-002）。

### Tests for User Story 2

- [ ] T017 [P] [US2] Test `get_all_tags()` returns all tags from `tags` table in `tests/test_tags.py`
- [ ] T018 [P] [US2] Test `get_all_tags(include_categories=True)` returns categories too in `tests/test_tags.py`
- [ ] T019 [P] [US2] Test `get_all_tags(include_categories=False)` excludes categories in `tests/test_tags.py`
- [ ] T020 [P] [US2] Test `get_all_tags()` returns correct `asset_count` per tag in `tests/test_tags.py`
- [ ] T021 [P] [US2] Test `get_all_tags()` handles empty database (no tags) gracefully in `tests/test_tags.py`

### Implementation for User Story 2

> Implementation already exists (`get_all_tags` function). Verify correctness.

- [ ] T022 [US2] Verify `get_all_tags()` total count matches `SELECT COUNT(*) FROM tags` + `SELECT COUNT(*) FROM categories` in `.kimi/skills/cang_tag_search/main.py`

**Checkpoint**: User Story 1 AND 2 both functional. Tag discovery complete.

---

## Phase 5: User Story 3 — 提取结构化证据片段 (Priority: P3)

**Goal**: 从检索到的知识资产中提取按主题过滤的结构化证据片段，附带来源追溯。

**Independent Test**: `extract_evidence(asset, themes=["疗效数据"])` 返回 `EvidenceResult`，包含匹配主题的片段和来源追溯。

### Tests for User Story 3

- [ ] T023 [P] [US3] Test `extract_evidence()` uses `analysis_results` when `analysis_result_id` is present in `tests/test_extract.py`
- [ ] T024 [P] [US3] Test `extract_evidence()` falls back to `description/content_text` when no analysis_results in `tests/test_extract.py`
- [ ] T025 [P] [US3] Test `extract_evidence()` with theme filtering returns only matching themes in `tests/test_extract.py`
- [ ] T026 [P] [US3] Test `extract_evidence()` handles missing PDF gracefully (Tier 2 fail → Tier 3) in `tests/test_extract.py`
- [ ] T027 [P] [US3] Test `extract_evidence()` returns `themes_found` and `themes_missing` correctly in `tests/test_extract.py`
- [ ] T028 [P] [US3] Test `extract_evidence()` handles `asset=None` gracefully in `tests/test_extract.py`
- [ ] T029 [P] [US3] Test `extract_evidence()` fragments include source traceability fields (`asset_id`, `source_pdf`, `extraction_method`) in `tests/test_extract.py`

### Implementation for User Story 3

> Implementation already exists (`extract_evidence` function). Verify correctness.

- [ ] T030 [US3] Verify three-tier extraction order (analysis_results → pdf-distiller → description) in `.kimi/skills/cang_tag_search/main.py`

**Checkpoint**: All three user stories fully functional and testable independently.

---

## Phase 6: Integration & Validation

**Purpose**: End-to-end validation against real production database.

- [ ] T031 Run CLI smoke test: `python main.py tags` against production database
- [ ] T032 Run CLI smoke test: `python main.py search 阿尔茨海默病` against production database
- [ ] T033 Run CLI smoke test: `python main.py extract <real_asset_id> 疗效数据` against production database
- [ ] T034 [P] Verify log output in `logs/cang-tag-search-YYYY-MM-DD.jsonl` contains correct operation types and timestamps
- [ ] T035 [P] Verify `PYTHONPATH=/root/huidu/.kimi/skills python -c "from cang_tag_search import ..."` import works from any directory
- [ ] T036 Run all tests: `cd .kimi/skills/cang_tag_search && pytest -v`

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ✅ DONE
    │
Phase 2 (Pytest Infra) ── BLOCKS all user story tests
    │
    ├── Phase 3 (US1 - P1) 🎯 MVP
    ├── Phase 4 (US2 - P2)     (can start in parallel)
    └── Phase 5 (US3 - P3)     (can start in parallel)
    │
Phase 6 (Integration) ── Depends on all stories
```

### Within Each User Story

- Tests FIRST (T009-T014 for US1 → should FAIL before verification)
- Verification AFTER tests pass
- All tests within a story marked `[P]` can run in parallel

### Parallel Opportunities

```
Phase 2:
  T006 + T007 (different files, independent)

Phase 3 (US1):
  T009 ┬┈ T010 ┬┈ T011 ┬┈ T012 ┬┈ T013 ┬┈ T014 (all independent)
  Then T015 → T016 (sequential verification)

Phase 4 (US2):
  T017 ┬┈ T018 ┬┈ T019 ┬┈ T020 ┬┈ T021 (all independent)
  Then T022

Phase 5 (US3):
  T023 ┬┈ T024 ┬┈ T025 ┬┈ T026 ┬┈ T027 ┬┈ T028 ┬┈ T029 (all independent)
  Then T030
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Pytest Infrastructure
2. Complete Phase 3: User Story 1 (search tests + verification)
3. **STOP and VALIDATE**: All US1 tests pass
4. Skill is usable for basic tag search

### Incremental Delivery

1. Phase 2 → Test infrastructure ready
2. Phase 3 (US1) → Tag search works → **MVP!**
3. Phase 4 (US2) → Tag discovery works
4. Phase 5 (US3) → Evidence extraction works
5. Phase 6 → Production validation

### Current Status

**24 tasks total**, **5 completed** (Phase 1), **19 remaining** (Phases 2-6).

Tasks per user story:
- US1 (P1, MVP): 8 tasks (T009-T016)
- US2 (P2): 6 tasks (T017-T022)
- US3 (P3): 8 tasks (T023-T030)
- Infrastructure: 3 tasks (T006-T008)
- Integration: 6 tasks (T031-T036)

Parallel tasks: 20 of 24 tasks are marked `[P]` (different files, no dependencies).
