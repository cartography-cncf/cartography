# Cartography Documentation

## Local development

### One-time build

To build the documentation once:

```bash
uv sync --group doc
cd docs
./build.sh
```

The built documentation will be in `docs/generated/docs/`. Open `docs/generated/docs/index.html` in your browser.

### Live-reloading development server

For local development with auto-reload:

```bash
uv sync --group doc
cd docs
# First sync files from root/ to generated/rst/
rsync -av root/ conf.py generated/rst/
# Start the auto-build server, watching root/ for changes
uv run sphinx-autobuild generated/rst generated/docs --watch root/ --pre-build "rsync -av root/ conf.py generated/rst/" --port 8000
```

Then visit http://localhost:8000. Changes to files in `docs/root/` will automatically trigger a rebuild.
