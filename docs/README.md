# Cartography Documentation

## Local development

```bash
uv sync --group doc
uv run sphinx-autobuild docs/root docs/generated/docs -c docs --port 8000
```

Then visit http://localhost:8000. Changes to files in `docs/root/` will automatically trigger a rebuild.

## Markdown source aliases (`*.md.txt`)

The docs UI/AI integrations may request markdown source files using a `.txt` suffix (for example `config.md.txt`).

When you add or rename files under `docs/root/`, sync aliases with:

```bash
python docs/sync_markdown_txt_aliases.py
```

To validate only (used by pre-commit):

```bash
python docs/sync_markdown_txt_aliases.py --check
```
