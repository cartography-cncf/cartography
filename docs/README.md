# Cartography Documentation

## Local development

```bash
uv sync --group doc
uv run sphinx-autobuild docs/root docs/generated/docs -c docs --port 8000
```

Then visit http://localhost:8000. Changes to files in `docs/root/` will automatically trigger a rebuild.
