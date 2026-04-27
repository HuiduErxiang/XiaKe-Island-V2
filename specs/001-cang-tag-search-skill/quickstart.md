# Quick Start — Cang Tag Search Skill

**Feature**: 001-cang-tag-search-skill
**Date**: 2026-04-24

## Prerequisites

- Python 3.10+
- Material platform database accessible on local filesystem
- (Optional) pdf-distiller skill for Tier 2 evidence extraction

## Setup

```bash
cd /root/huidu/.kimi/skills/cang-tag-search

# Install dependencies
pip install pydantic

# Optional: for PDF extraction fallback
pip install -r requirements.txt
```

## Verify Database

```bash
ls -la /root/huidu/ai-awesome-material-platform/backend/database.sqlite
```

If the database is at a different path, set the env var:

```bash
export MATERIAL_PLATFORM_DB_PATH=/path/to/database.sqlite
export MATERIAL_PLATFORM_UPLOADS_DIR=/path/to/uploads
```

## Test the Skill

### 1. List all tags

```bash
cd /root/huidu/.kimi/skills/cang-tag-search
python -c "
import asyncio
from main import get_all_tags

async def main():
    result = await get_all_tags()
    print(f'Total tags: {result.total_count}')
    for t in result.tags[:20]:
        print(f'  [{t.type}] {t.name} ({t.asset_count} assets)')

asyncio.run(main())
"
```

### 2. Search by tag

```bash
python -c "
import asyncio
from main import search

async def main():
    result = await search(tags=['仑卡奈单抗', '阿尔茨海默病'])
    print(f'Found {result.total_matches} assets ({result.execution_time_ms}ms)')
    for a in result.assets:
        print(f'  [{a.match_count} matches] {a.name}')
        print(f'    Category: {a.category}')
        print(f'    Tags: {a.tags}')

asyncio.run(main())
"
```

### 3. Extract evidence

```bash
python -c "
import asyncio
from main import search, extract_evidence

async def main():
    results = await search(tags=['仑卡奈单抗'], max_results=5)
    if results.assets:
        evidence = await extract_evidence(
            asset=results.assets[0],
            themes=['疗效数据', '安全性数据']
        )
        print(f'Themes found: {evidence.themes_found}')
        print(f'Themes missing: {evidence.themes_missing}')
        for f in evidence.fragments[:5]:
            print(f'  [{f.theme}] ({f.extraction_method}) {f.content[:150]}...')

asyncio.run(main())
"
```

### 4. CLI

```bash
python main.py tags                          # List all tags
python main.py search 仑卡奈单抗 阿尔茨海默病   # Search
python main.py extract <asset_id> 疗效数据     # Extract evidence
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `MATERIAL_PLATFORM_DB_PATH` | `ai-awesome-material-platform/backend/database.sqlite` | SQLite database path |
| `MATERIAL_PLATFORM_UPLOADS_DIR` | `ai-awesome-material-platform/backend/uploads` | PDF uploads directory |
| `CANG_TAG_SEARCH_LOG_DIR` | `logs` | Log output directory |

## Logs

```bash
# View today's logs
cat logs/cang-tag-search-$(date +%Y-%m-%d).jsonl | head -20

# Each line is a JSON object:
# {"timestamp":"...","operation":"search","input_tags":["..."],"result_count":5,"execution_time_ms":45}
```
