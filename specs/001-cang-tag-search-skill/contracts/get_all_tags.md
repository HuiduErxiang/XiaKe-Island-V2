# Contract: `get_all_tags`

**Module**: `cang_tag_search`
**Function**: `async def get_all_tags(include_categories=True, config=None) -> TagList`

## Purpose

Discover all available tags and categories from the material platform database.

## Signature

```python
async def get_all_tags(
    include_categories: bool = True,
    config: Optional[SearchConfig] = None,
) -> TagList
```

## Input

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `include_categories` | `bool` | No | `True` | Also include categories as tags (type="category") |
| `config` | `SearchConfig \| None` | No | `None` | Override DB path |

## Output: `TagList`

```python
class TagList(BaseModel):
    tags: List[Tag]
    total_count: int
    source: str  # "database"

class Tag(BaseModel):
    id: str        # DB primary key
    name: str      # Tag name (unique)
    type: str      # "tag" | "category"
    asset_count: Optional[int]  # Linked assets count
```

## Behavior

- Queries `tags` + `material_tags` for tags
- Queries `categories` + `cang_materials` for categories (if `include_categories=True`)
- Returns empty `tags: []` if database has no tags (no error)
- Raises `FileNotFoundError` if database file doesn't exist

## Errors

| Condition | Response |
|-----------|----------|
| DB file not found | `FileNotFoundError` |
| Empty tags table | `TagList(tags=[], total_count=0)` |

## Logging

Each call writes a `SearchLogEntry` with `operation="get_all_tags"`.
