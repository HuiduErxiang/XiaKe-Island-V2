# Contract: `search`

**Module**: `cang_tag_search`
**Function**: `async def search(tags, max_results=None, config=None) -> SearchResult`

## Purpose

Search knowledge assets by tag names using OR logic, sorted by match count.

## Signature

```python
async def search(
    tags: List[str],
    max_results: Optional[int] = None,
    config: Optional[SearchConfig] = None,
) -> SearchResult
```

## Input

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tags` | `List[str]` | Yes | — | Tag names to search (OR logic) |
| `max_results` | `int \| None` | No | `20` | Max assets to return |
| `config` | `SearchConfig \| None` | No | `None` | Search config override |

## Output: `SearchResult`

```python
class SearchResult(BaseModel):
    assets: List[KnowledgeAsset]
    total_matches: int         # Total before LIMIT
    query_tags: List[str]      # Echo of input tags
    execution_time_ms: int     # Wall-clock query time
```

## Search Algorithm

1. Match input tag names against `tags.name` (exact + case-insensitive)
2. Find all `cang_materials` linked via `material_tags` where `type = 'document'`
3. Count matched tags per asset (`match_count`)
4. Sort: `match_count DESC, cang_materials.updated_at DESC`
5. Limit results to `max_results`

## Behavior

- Empty `tags` list → `SearchResult(assets=[], total_matches=0)`
- No matching tags in DB → `SearchResult(assets=[], total_matches=0)`
- Never raises exceptions for no-match (spec FR-006)

## Errors

| Condition | Response |
|-----------|----------|
| DB file not found | `FileNotFoundError` |
| `tags` is empty list | `SearchResult(assets=[], total_matches=0)` |
| No tag match | `SearchResult(assets=[], total_matches=0)` |

## Logging

Each call writes a `SearchLogEntry` with `operation="search"`, `input_tags`, `result_count`, `execution_time_ms`.
