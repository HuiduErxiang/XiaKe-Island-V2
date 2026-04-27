# Data Model — Cang Tag Search Skill

**Feature**: 001-cang-tag-search-skill
**Date**: 2026-04-24

## Entity Relationship Diagram

```
tags ──┐
       ├── material_tags ──┬── cang_materials ──┬── categories
       │   (material_id)    │   (category_id)    │
       │   (tag_id)         │                    │
       └────────────────────┘                    │
                                                 │
                            analysis_results ────┘
                            (material_id via
                             analysis_result_id)
```

## Entities

### Tag

A searchable keyword or category label.

| Field | Type | Source Table | Notes |
|-------|------|-------------|-------|
| `id` | `str` | `tags.id` | Primary key |
| `name` | `str` | `tags.name` | Unique, case-sensitive |
| `type` | `"tag" \| "category"` | derived | Based on source table |
| `asset_count` | `int \| None` | COUNT via `material_tags` | Number of linked assets |

**Validation**: `name` is non-empty. `asset_count` >= 0.

**Source SQL**:
```sql
-- Tags
SELECT t.id, t.name, COUNT(mt.material_id) as asset_count
FROM tags t
LEFT JOIN material_tags mt ON t.id = mt.tag_id
GROUP BY t.id, t.name

-- Categories (as tags)
SELECT c.id, c.name, COUNT(cm.id) as asset_count
FROM categories c
LEFT JOIN cang_materials cm ON c.id = cm.category_id
GROUP BY c.id, c.name
```

---

### KnowledgeAsset

A document-type material in the knowledge base.

| Field | Type | Source Column | Notes |
|-------|------|--------------|-------|
| `id` | `str` | `cang_materials.id` | PK, UUID format |
| `name` | `str` | `cang_materials.name` | Display name |
| `category` | `str \| None` | `categories.name` | Joined via `category_id` |
| `category_id` | `str \| None` | `cang_materials.category_id` | FK → categories |
| `url` | `str \| None` | `cang_materials.url` | File path relative to uploads/ |
| `tags` | `List[str]` | `tags.name` via `material_tags` | All associated tags |
| `match_count` | `int` | COUNT of matched tags | How many query tags matched |
| `match_tags` | `List[str]` | matched `tags.name` | Which query tags matched |
| `file_hash` | `str \| None` | `cang_materials.file_hash` | SHA256 |
| `description` | `str \| None` | `cang_materials.description` | User-provided description |
| `content_text` | `str \| None` | `cang_materials.content_text` | Extracted text |
| `uploaded_at` | `datetime \| None` | `cang_materials.uploaded_at` | Upload timestamp |
| `updated_at` | `datetime \| None` | `cang_materials.updated_at` | Last update |
| `analysis_status` | `str \| None` | `cang_materials.analysis_status` | pending/analyzing/completed/failed |
| `analysis_result_id` | `str \| None` | `cang_materials.analysis_result_id` | FK → analysis_results |

**Query filter**: Only `type = 'document'` materials are returned.

**Sort rule**: `match_count DESC, updated_at DESC` (spec FR-005: tag match count is primary sort; category relevance sort deferred per spec note).

---

### EvidenceFragment

A structured evidence snippet extracted from an asset.

| Field | Type | Notes |
|-------|------|-------|
| `theme` | `str` | Theme label, e.g. "疗效数据", "安全性数据" |
| `content` | `str` | Extracted text (capped at 2000 chars) |
| `source_pdf` | `str \| None` | PDF filename (`cang_materials.url`) |
| `source_path` | `str \| None` | Resolved absolute filesystem path |
| `asset_id` | `str` | FK → `cang_materials.id` |
| `asset_name` | `str \| None` | Display name for traceability |
| `extracted_at` | `datetime` | UTC timestamp of extraction |
| `extraction_method` | `str` | `analysis_results` \| `pdf_distiller` \| `description` |

**Missing from current schema but referenced in spec**:
- `relevance_score` (spec Key Entity `EvidenceFragment.相关性分数`): Not yet implemented. Deferred — current sorting relies on extraction method priority, not per-fragment scoring.

---

### SearchResult

Wrapper for search results.

| Field | Type | Notes |
|-------|------|-------|
| `assets` | `List[KnowledgeAsset]` | Matching assets |
| `total_matches` | `int` | Total before LIMIT |
| `query_tags` | `List[str]` | Input tags for traceability |
| `execution_time_ms` | `int` | Query wall-clock time |

---

### EvidenceResult

Wrapper for extraction results.

| Field | Type | Notes |
|-------|------|-------|
| `asset_id` | `str` | Source asset |
| `asset_name` | `str \| None` | Source name |
| `fragments` | `List[EvidenceFragment]` | Extracted fragments |
| `themes_found` | `List[str]` | Themes with results |
| `themes_missing` | `List[str]` | Themes without results |
| `execution_time_ms` | `int` | Extraction wall-clock time |

---

## Configuration Models

### SearchConfig

| Field | Type | Default | Range |
|-------|------|---------|-------|
| `max_results` | `int` | 20 | [1, 100] |
| `include_analysis_results` | `bool` | True | — |
| `sort_by` | `str` | "relevance" | relevance \| date \| name |
| `db_path` | `str \| None` | None (auto-detect) | — |

### EvidenceConfig

| Field | Type | Default | Range |
|-------|------|---------|-------|
| `themes` | `List[str]` | [] | — |
| `use_analysis_results_first` | `bool` | True | — |
| `max_fragments_per_theme` | `int` | 5 | [1, 20] |
| `uploads_dir` | `str \| None` | None (auto-detect) | — |
| `db_path` | `str \| None` | None (auto-detect) | — |

---

## Database Tables (Read-Only)

The skill performs **read-only** queries against these material platform tables:

| Table | Accessed By | Key Columns Used |
|-------|------------|-----------------|
| `tags` | `get_all_tags`, `search` | `id`, `name` |
| `categories` | `get_all_tags` | `id`, `name` |
| `cang_materials` | `search`, `extract_evidence` | `id`, `name`, `type`, `category_id`, `url`, `description`, `content_text`, `file_hash`, `uploaded_at`, `updated_at`, `analysis_status`, `analysis_result_id` |
| `material_tags` | `get_all_tags`, `search` | `material_id`, `tag_id` |
| `analysis_results` | `extract_evidence` | `id`, `content`, `result_type`, `status` |

No tables are created, altered, or written by this skill.
