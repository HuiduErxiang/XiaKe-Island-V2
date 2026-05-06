# Tasks: 产品审核子 Agent Skill

**Input**: Design documents from `specs/003-product-review-skill/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/skill-api.md

**Tests**: Included per spec acceptance scenarios and research.md testing strategy.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths in descriptions

## Path Conventions

All source code under `.claude/skills/product-review/`, tests under `.claude/skills/product-review/test/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton and dependency declaration

- [ ] T001 Create directory structure for `.claude/skills/product-review/` including `test/fixtures/evidence_review/`, `test/fixtures/prd_review/`, `test/fixtures/edge_cases/`
- [ ] T002 Create `requirements.txt` in `.claude/skills/product-review/requirements.txt` with `pydantic>=2.0.0` dependency

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema definitions that ALL user stories depend on — Pydantic models are the interface contract

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create all Pydantic models, enums, and validators in `.claude/skills/product-review/schema.py` — includes ReviewRequest, EvidenceFragment, ReviewConfig, ReviewResult, Finding, SupplementHint, RewriteTarget, ReviewError, plus mode-dependent field validators
- [ ] T004 [P] Create SKILL.md in `.claude/skills/product-review/SKILL.md` documenting the Skill purpose, two modes, and interface contract for colleague integration

**Checkpoint**: Schema contract ready — user story implementation can now begin

---

## Phase 3: User Story 1 - 证据审核：判断提取到的证据是否充分覆盖写作需求 (Priority: P1) 🎯 MVP

**Goal**: Evidence review mode — detect information points from writing requirement, calculate evidence coverage, output sufficiency judgment and supplement hints

**Independent Test**: Call `review(mode="evidence_review", writing_requirement=..., evidence_fragments=...)` and verify sufficiency status matches expected level for known evidence sets

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] [US1] Create evidence review test fixtures — `sufficient_evidence.json`, `partial_evidence.json`, `insufficient_evidence.json` in `.claude/skills/product-review/test/fixtures/evidence_review/`
- [ ] T006 [P] [US1] Write evidence review unit tests in `.claude/skills/product-review/test/test_evidence_review.py` covering all 4 acceptance scenarios (sufficient, partial, insufficient, empty evidence) from spec.md

### Implementation for User Story 1

- [ ] T007 [US1] Implement information point detection (8 predefined types with keyword mapping) in `.claude/skills/product-review/reviewer.py`
- [ ] T008 [US1] Implement evidence coverage calculation (covered/partial/missing per info point, ≥2/1/0 evidence hits) in `.claude/skills/product-review/reviewer.py`
- [ ] T009 [US1] Implement sufficiency judgment (sufficient/partial/insufficient based on coverage ratio) and supplement_hints generation in `.claude/skills/product-review/reviewer.py`

**Checkpoint**: Evidence review mode fully functional — can judge sufficiency and generate supplement hints

---

## Phase 4: User Story 2 - PRD 审核：审核撰写完成的 PRD 草稿质量 (Priority: P2)

**Goal**: PRD review mode — detect defects in PRD draft (logic gaps, unsupported claims, compliance issues, structure problems), output verdict and rewrite targets

**Independent Test**: Call `review(mode="prd_review", writing_requirement=..., prd_content=...)` and verify verdict matches expected result for known PRD content

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US2] Create PRD review test fixtures — `passed_prd.json`, `revision_prd.json` in `.claude/skills/product-review/test/fixtures/prd_review/`
- [ ] T011 [P] [US2] Write PRD review unit tests in `.claude/skills/product-review/test/test_prd_review.py` covering all 4 acceptance scenarios (passed, revision_required for logic gaps, critical for compliance, empty PRD) from spec.md

### Implementation for User Story 2

- [ ] T012 [US2] Implement 4-class PRD defect detection (argument_without_evidence, logic_gap, structure_missing, compliance_redline) in `.claude/skills/product-review/reviewer.py`
- [ ] T013 [US2] Implement PRD verdict judgment (passed/revision_required based on high/critical findings) and rewrite_targets generation in `.claude/skills/product-review/reviewer.py`

**Checkpoint**: PRD review mode fully functional — can judge PRD quality and generate rewrite targets

---

## Phase 5: User Story 3 - Mock 模式：以确定性输出支持 Pipeline 联调 (Priority: P3)

**Goal**: Wire up entry point, enforce schema validation, guarantee deterministic output, enable colleague to replace mock internals without breaking Pipeline

**Independent Test**: Same input called twice produces identical output; Pydantic schema validation passes for all fixtures; colleague-only `reviewer.py` replacement leaves Pipeline intact

### Implementation for User Story 3

- [ ] T014 [US3] Create edge case test fixtures — `empty_requirement.json`, `invalid_mode.json`, `malformed_evidence.json`, `truncated_prd.json`, `language_mismatch.json` in `.claude/skills/product-review/test/fixtures/edge_cases/` — covers spec edge cases: empty input, invalid mode, malformed evidence, PRD >50000 chars with `truncated_review` flag, CN requirement + EN evidence
- [ ] T015 [US3] Implement input validation and mode dispatch in `.claude/skills/product-review/main.py` — validate mode, check mode-required fields, handle empty/invalid input per FR-015
- [ ] T016 [US3] Implement `review()` entry point and output assembly in `.claude/skills/product-review/main.py` — orchestrate reviewer, assemble ReviewResult, inject schema_version
- [ ] T017 [P] [US3] Create `__init__.py` in `.claude/skills/product-review/__init__.py` exporting `review` as the single public API

### Tests for User Story 3

- [ ] T018 [P] [US3] Write schema validation tests in `.claude/skills/product-review/test/test_schema.py` — Pydantic model positive/negative cases, all validators, enum constraints
- [ ] T019 [US3] Write determinism tests in `.claude/skills/product-review/test/test_determinism.py` — same input 10 calls produces identical output; covers both modes
- [ ] T020 [US3] Write integration tests in `.claude/skills/product-review/test/test_integration.py` — full `review()` call chain for both modes, error response paths

**Checkpoint**: All user stories independently functional with deterministic output and verified schema compliance

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and quality assurance

- [ ] T021 Run full test suite with pytest, verify all tests pass and spec requirements are met:
  - SC-002: Schema validation coverage 100%
  - SC-003: Determinism across 10 identical calls for both modes
  - SC-004: Evidence sufficiency accuracy per acceptance scenarios
  - SC-005: PRD verdict accuracy per acceptance scenarios
  - SC-001: Performance benchmark — single review (5 evidence fragments, 3000-char requirement) completes in <1s (add `pytest --durations=0` or explicit time assertion)
  - SC-006: Colleague replaceability — verify no imports or assumptions leak between `schema.py`/`main.py` and `reviewer.py` internals (code-review gate, not automated)
- [ ] T022 Validate quickstart.md scenarios execute correctly against the implemented Skill

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T003, schema.py)
- **User Story 2 (Phase 4)**: Depends on Foundational (T003, schema.py) — independent from US1
- **User Story 3 (Phase 5)**: Depends on US1 + US2 (reviewer.py must be complete for main.py orchestration)
- **Polish (Phase 6)**: Depends on all phases complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 — Independent from US1 (different reviewer.py functions)
- **User Story 3 (P3)**: Depends on US1 + US2 — main.py orchestrates both modes

### Within Each User Story

- Tests (fixtures + test file) written FIRST and must FAIL before implementation
- Evidence review: info point detection → coverage calc → sufficiency + hints
- PRD review: defect detection → verdict + rewrite targets
- Entry point: validation → orchestration → assembly

### Parallel Opportunities

- T003 (schema.py) and T004 (SKILL.md) can run in parallel within Phase 2
- T005 (evidence fixtures) and T006 (evidence tests) can run in parallel within US1 tests
- T010 (PRD fixtures) and T011 (PRD tests) can run in parallel within US2 tests
- T017 (__init__.py), T018 (schema tests) can run in parallel within Phase 5
- US1 and US2 implementation phases can run in parallel (different reviewer.py functions)
- All test fixtures within a phase marked [P] can be created in parallel

---

## Parallel Example: Phase 5 (US3)

```bash
# Launch independent US3 tasks together (after T014-T016 complete):
Task: "Create __init__.py in .claude/skills/product-review/__init__.py"
Task: "Write schema validation tests in .claude/skills/product-review/test/test_schema.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T004)
3. Complete Phase 3: User Story 1 — Evidence Review (T005-T009)
4. **STOP and VALIDATE**: Test evidence review mode independently with fixtures
5. Deploy/demo — evidence review is the first quality gate in the Product Agent pipeline

### Incremental Delivery

1. Setup + Foundational → Schema contract ready
2. Add US1 (Evidence Review) → Test independently → MVP: evidence sufficiency judgment
3. Add US2 (PRD Review) → Test independently → Full review capability
4. Add US3 (Entry Point + Determinism) → Test independently → Pipeline-ready
5. Each story adds value without breaking previous stories

### 👤 Colleague Integration

After T021 (full test pass), the Skill is ready for colleague handoff:
- Colleague **replaces** `reviewer.py` internals (can swap keyword matching for LLM/rule-engine)
- Colleague **must not modify** `schema.py`, `main.py`, `__init__.py`, `SKILL.md`
- Colleague extends schema by adding optional fields to `schema.py` and bumping minor schema_version
- All existing tests must continue to pass after colleague modifications

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- `schema.py` and `main.py` are immutable interface contracts — only `reviewer.py` is replaceable
- Total estimated: ~830 lines source + ~350 lines test
