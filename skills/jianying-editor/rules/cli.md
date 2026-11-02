---
name: cli-tools
description: CLI tools for diagnostics, draft inspection, search, and export.
metadata:
  tags: cli, diagnostics, drafts, export
---

# CLI Tools

Prefer these scripts for command-line workflows.

## 1) Draft Inspector (Recommended)

Use `draft_inspector.py` to inspect local drafts quickly.

```bash
# list drafts
python <SKILL_ROOT>/scripts/draft_inspector.py list --limit 20

# summary by draft name
python <SKILL_ROOT>/scripts/draft_inspector.py summary --name "DraftName"

# show full draft JSON
python <SKILL_ROOT>/scripts/draft_inspector.py show --name "DraftName" --kind content --json
python <SKILL_ROOT>/scripts/draft_inspector.py show --name "DraftName" --kind meta --json
```

Notes:

- 本项目 `--root` 仅用于已核验的本机草稿目录，不得用它选择其他正式草稿位置；优先省略并使用本机记录。
- `--path` 只作当前电脑的原生草稿检查，不将其绝对值写入共享项目配置。
- `--json` returns machine-readable payload.

## 2) Diagnostics

```bash
python <SKILL_ROOT>/scripts/api_validator.py --json
```

## 3) Asset Search

```bash
python <SKILL_ROOT>/scripts/asset_search.py "复古" -c filters
python <SKILL_ROOT>/scripts/asset_search.py "雾化" -c transitions
```

## 4) Export

```bash
python <SKILL_ROOT>/scripts/auto_exporter.py "DraftName" "output.mp4" --res 1080 --fps 60
```

## 5) CLI Output Contract

For scripts supporting `--json`, prefer:

```json
{
  "ok": true,
  "code": "ok",
  "reason": "",
  "data": {}
}
```
