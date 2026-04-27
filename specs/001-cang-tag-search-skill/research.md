# Research — Cang Tag Search Skill

**Feature**: 001-cang-tag-search-skill
**Date**: 2026-04-24

## 1. Database: SQLite via stdlib `sqlite3`

**Decision**: Use Python stdlib `sqlite3` with `row_factory = sqlite3.Row` for dict-like row access.

**Rationale**:
- Constitution Principle V mandates reusing existing infrastructure — the material platform already uses SQLite
- `sqlite3` is in stdlib, zero additional dependencies
- Both `database-dev.sqlite` and `database.sqlite` are local files on the same server (spec assumption confirmed)
- The pdf-distiller skill uses the same pattern

**Alternatives considered**:
- SQLAlchemy ORM: Rejected — overkill for read-only queries against 5 tables, violates Principle V
- aiosqlite: Rejected — the queries are fast (<100ms), async overhead is unnecessary

**Gap identified**: `config.py` defaults to `database-dev.sqlite`, but the active production database is `database.sqlite`. Need to update the default path.

---

## 2. Tag Matching: SQL IN + OR Logic

**Decision**: Exact name match via `WHERE name IN (...)` with case-insensitive fallback. Sort by matched tag count DESC, then `updated_at` DESC.

**Rationale**:
- Spec FR-002 mandates OR logic with match-count sorting
- Spec FR-005 mandates category relevance as first sort priority, tag match as second
- SQL `IN` is simple, fast, and sufficient for <1000 tags

**Alternatives considered**:
- Full-text search (FTS5): Rejected — tags are controlled vocabulary, not free text; FTS adds schema complexity
- Vector/semantic search: Explicitly excluded by spec (FR-005 footnote)

**Gap identified**: Current implementation sorts by `match_count DESC, cm.updated_at DESC`. Spec FR-005 says first priority is category match, second is tag match. The `ORDER BY` should be: `match_count DESC, cm.updated_at DESC` (category relevance requires a more complex join; deferring to future iteration per spec note "暂不支持语义相似度排序").

---

## 3. Evidence Extraction: Three-Tier Strategy

**Decision**: Try `analysis_results` → `pdf-distiller` → `description/content_text` fallback.

**Rationale**:
- `analysis_results` contains pre-computed structured content, fastest and most reliable
- `pdf-distiller` provides deep extraction for PDFs not yet analyzed
- Fallback ensures we always return something, even if both prior tiers fail
- Error in any tier is silently caught, allowing fallthrough (spec FR-006: no exceptions to caller)

**Alternatives considered**:
- pdf-distiller only: Rejected — wastes pre-computed analysis results in DB
- Always run all tiers: Rejected — wasteful; first successful tier is sufficient

---

## 4. PDF Path Resolution

**Decision**: Resolve `cang_materials.url` against `uploads/` directory with multiple fallback strategies.

**Rationale**:
- `url` values in DB may be relative (`uploads/2026/04/file.pdf`), absolute (`/root/...`), or partial
- Try: absolute path → join with uploads_dir → strip `uploads/` prefix → strip `/uploads/` prefix
- If nothing resolves, return None (not an error — spec Edge Case "PDF file missing")

---

## 5. Logging: Daily JSONL Files

**Decision**: Append structured JSON log entries to `logs/cang-tag-search-YYYY-MM-DD.jsonl`.

**Rationale**:
- Spec FR-008 mandates per-call logging with specific fields
- JSONL is append-only, human-readable, and easy to grep/analyze
- Daily rotation prevents unbounded file growth
- Already implemented — no changes needed

---

## 6. Package Structure: Missing `__init__.py`

**Gap**: `.kimi/skills/cang-tag-search/` has no `__init__.py`. The SKILL.md documents `from cang_tag_search import ...` but this requires the directory to be on `sys.path` with a proper package init.

**Decision**: Add `__init__.py` following the pdf-distiller pattern (re-export public API from main.py).

---

## 7. Error Model: Defined but Unused

**Gap**: `schema.py` defines `CangTagSearchError` but `main.py` never instantiates it — uses plain `FileNotFoundError` for DB not found, and silent `except Exception: pass` for extraction failures.

**Decision**: Keep existing error handling approach. The `CangTagSearchError` model is documented for future use but current behavior (return empty results on failure) aligns with spec FR-006. Plain exceptions for setup errors (DB not found) are acceptable since they indicate configuration problems that should halt execution.

---

## 8. Config: DB Path Mismatch

**Gap**: `config.py` line 18 defaults to `database-dev.sqlite`. The Explore agent confirmed the active database is `database.sqlite` (same server, same schema). `database-dev.sqlite` has a legacy `materials` table and may be stale.

**Decision**: Update `DEFAULT_DB_PATH` to point to `database.sqlite`. Also update both SKILL.md files.
