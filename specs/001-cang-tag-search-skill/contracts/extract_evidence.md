# Contract: `extract_evidence`

**Module**: `cang_tag_search`
**Function**: `async def extract_evidence(asset, themes=None, config=None) -> EvidenceResult`

## Purpose

Extract structured evidence fragments from a knowledge asset using a three-tier strategy.

## Signature

```python
async def extract_evidence(
    asset: KnowledgeAsset,
    themes: Optional[List[str]] = None,
    config: Optional[EvidenceConfig] = None,
) -> EvidenceResult
```

## Input

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `asset` | `KnowledgeAsset` | Yes | — | Asset to extract from |
| `themes` | `List[str] \| None` | No | `[]` | Theme filters |
| `config` | `EvidenceConfig \| None` | No | `None` | Extraction config |

## Output: `EvidenceResult`

```python
class EvidenceResult(BaseModel):
    asset_id: str
    asset_name: Optional[str]
    fragments: List[EvidenceFragment]
    themes_found: List[str]
    themes_missing: List[str]
    execution_time_ms: int
```

## Extraction Strategy (Three-Tier)

### Tier 1: `analysis_results` (DB)
- If `asset.analysis_result_id` exists and `use_analysis_results_first=True`
- Query `analysis_results` WHERE `status = 'completed'`
- Parse content as JSON, extract fields matching requested themes

### Tier 2: `pdf-distiller` (external skill)
- If `asset.url` resolves to an existing PDF
- Import and call `pdf_distiller.extract_sync()`
- Map `ExtractedContent` fields to themes

### Tier 3: `description` / `content_text` (fallback)
- Use `content_text` or `description` from the asset itself
- Simple text extraction for requested themes

## Behavior

- `asset` is None → `EvidenceResult(asset_id="", fragments=[])`
- Theme matching is case-insensitive
- Content capped at 2000 chars per fragment
- Each tier failure silently falls through to next tier
- Reports `themes_found` and `themes_missing`

## Errors

| Condition | Response |
|-----------|----------|
| All tiers fail | `EvidenceResult` with `fragments=[]` |
| pdf-distiller import error | Falls through to Tier 3 |
| DB query error | Falls through to next tier |

## Logging

Each call writes a `SearchLogEntry` with `operation="extract_evidence"`, evidence sources, fragment count, `execution_time_ms`.
