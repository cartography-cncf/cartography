#!/bin/sh
while ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; do
  echo "Waiting for Git to be ready..."
  sleep 1
done
# Pass control to main container command
exec "$@"
