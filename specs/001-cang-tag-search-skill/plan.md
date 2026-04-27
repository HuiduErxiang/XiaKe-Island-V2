# Implementation Plan: 藏经阁标签检索 Skill

**Branch**: `001-cang-tag-search-skill` | **Date**: 2026-04-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-cang-tag-search-skill/spec.md`

## Summary

Implement a knowledge retrieval Skill that bridges the material platform SQLite database and the multi-agent writing pipeline. The Skill provides three capabilities: (1) tag discovery from the material platform's `tags` + `categories` tables, (2) OR-logic tag search across `cang_materials` via `material_tags` join, and (3) three-tier evidence extraction (analysis_results → pdf-distiller → description fallback).

**Key finding**: The Skill already has a ~610-line implementation at `.kimi/skills/cang_tag_search/` with all three core functions working. This plan focuses on: fixing identified gaps, adding missing package infrastructure, updating the database path default, and writing tests.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: pydantic 2.x, sqlite3 (stdlib), pdf-distiller (optional)
**Storage**: SQLite (material platform `database.sqlite`, read-only access)
**Testing**: pytest (to be added)
**Target Platform**: Linux server (same server as material platform)
**Project Type**: Python library + CLI
**Performance Goals**: <500ms per search, <2s per evidence extraction
**Constraints**: Read-only DB access, no new tables, zero added infra dependencies
**Scale/Scope**: ~309 unique PDFs, ~50 tags, ~15 categories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I - Protected Master Branch
- [x] Feature branch `001-cang-tag-search-skill` created from `master`
- [x] Branch naming follows `feature/xxx-描述` convention (via speckit scripts)

### Principle II - Feature Branch Workflow
- [x] Plan documents target branch for implementation
- [x] No direct commits to `master` anticipated in this plan

### Principle III - Dual Environment Deployment
- [x] N/A — This Skill runs as a Python module with no HTTP ports. The DB path is configurable via env var, supporting both dev (`database-dev.sqlite`) and prod (`database.sqlite`) environments.

### Principle IV - Deployment Gatekeeping
- [x] N/A — This Skill is not deployed independently; it is imported as a library by the XiaKe-Island orchestrator. No `deploy.sh` involved.

### Principle V - Minimum Invasive Changes
- [x] New dependencies justified: only `pydantic` (already used by pdf-distiller and material platform)
- [x] Database schema changes: N/A (read-only access)
- [x] No new architecture patterns introduced — follows existing `.kimi/skills/` conventions (pdf-distiller pattern)

**Complexity Tracking**: No violations. Table is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-cang-tag-search-skill/
├── plan.md              # This file
├── research.md          # Phase 0: Technical decisions & gap analysis
├── data-model.md        # Phase 1: Entity definitions & DB mapping
├── quickstart.md        # Phase 1: Quick start guide
├── contracts/           # Phase 1: API contracts
│   ├── get_all_tags.md
│   ├── search.md
│   └── extract_evidence.md
├── checklists/
│   └── requirements.md  # Pre-existing quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (actual location)

```text
.kimi/skills/cang_tag_search/
├── SKILL.md             # Human-readable documentation
├── main.py              # Public API + CLI (610 lines, exists)
├── config.py            # SkillConfig (73 lines, exists)
├── schema.py            # Pydantic data models (128 lines, exists)
├── __init__.py          # Package init (added v1.1.0)
├── requirements.txt     # Dependencies (added v1.1.0)
└── logs/                # Runtime logs (JSONL, auto-created)
```

**Structure Decision**: The Skill lives in `.kimi/skills/cang_tag_search/` following the existing pdf-distiller pattern. It is NOT under `XiaKe-Island-V2/src/` — this is by design: Skills are shared across projects (used by both product_agent and writing_agent), not coupled to a single orchestrator.

## Gaps Identified (from Research)

| # | Gap | Severity | Action |
|---|-----|----------|--------|
| 1 | `config.py` defaults to `database-dev.sqlite` instead of active `database.sqlite` | Medium | Update `DEFAULT_DB_PATH` in config.py, update both SKILL.md files |
| 2 | Missing `__init__.py` — no clean `from cang_tag_search import ...` | Medium | Add `__init__.py` following pdf-distiller pattern |
| 3 | `CangTagSearchError` model defined but never used | Low | Leave as-is; model is documented for future use |
| 4 | `EvidenceFragment` missing `relevance_score` field from spec | Low | Defer — current tier-priority approach is sufficient |
| 5 | `SearchResult` does not document sort method in output | Low | Defer — `match_count` field implicitly documents sort |
| 6 | No tests | Medium | Add pytest test suite |
| 7 | No `requirements.txt` | Low | Add requirements.txt |

## Implementation Phases

### Phase 1: Fix Identified Gaps
- Update `DEFAULT_DB_PATH` from `database-dev.sqlite` → `database.sqlite`
- Add `__init__.py` with public API re-exports
- Add `requirements.txt`
- Update SKILL.md files to reflect correct DB path

### Phase 2: Tests
- Add `tests/` directory with pytest suite
- Test: `get_all_tags` returns tags with correct structure
- Test: `search` with matching/non-matching/multi tags
- Test: `extract_evidence` fallback chain
- Test: Empty/null input handling
- Test: Missing DB error handling

### Phase 3: Integration Validation
- Run CLI smoke tests against production database
- Verify integration with product_agent orchestration flow
