# Cartography Documentation

Module schema pages (`modules/*/schema.md`) are generated from the declarative data
model at build time, so they must never be written into `docs/root/`. Both commands
below build from `generated/rst/`, a throwaway copy of the sources.

## One-off build

```bash
uv sync --group doc
uv run ./docs/build.sh
```

The rendered site lands in `generated/docs`.

## Live reload

```bash
uv sync --group doc
uv run sphinx-autobuild \
  --pre-build 'rsync -a docs/root/ docs/conf.py generated/rst/' \
  --watch docs/root --watch cartography \
  --port 8000 \
  generated/rst generated/docs
```

Then visit http://localhost:8000. Editing `docs/root/` triggers a rebuild, and so does
editing a model under `cartography/` since that is where schema pages come from.
