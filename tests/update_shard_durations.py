"""Merge per-shard duration files into ``tests/shard_durations.json``.

Each CI shard (or a local run) records its per-file durations when
``CARTOGRAPHY_STORE_SHARD_DURATIONS`` is set. Pass those files here:

    uv run python -m tests.update_shard_durations shard-durations-*.json
"""

import json
import sys
from pathlib import Path

from tests.sharding import DURATIONS_FILE


def main(paths: list[str]) -> None:
    merged: dict[str, float] = {}
    for path in paths:
        for test_file, seconds in json.loads(Path(path).read_text()).items():
            merged[test_file] = merged.get(test_file, 0.0) + seconds
    DURATIONS_FILE.write_text(
        json.dumps(
            {f: round(s, 2) for f, s in sorted(merged.items())},
            indent=2,
        )
        + "\n",
    )
    print(f"Wrote {len(merged)} file durations to {DURATIONS_FILE}")


if __name__ == "__main__":
    main(sys.argv[1:])
