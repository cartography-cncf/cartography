#!/bin/sh
while ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; do
  echo "Waiting for Git to be ready..."
  sleep 1
done
# Activate the virtual environment
# This allow to used the virtual environment without having to specify `uv run`
. .venv/bin/activate
# Pass control to main container command
exec "$@"
