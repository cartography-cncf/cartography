"""Split a test run across CI jobs, one whole test file at a time.

Integration tests share a module-scoped Neo4j session and only wipe the graph when a
module finishes, so a file is the smallest unit that can safely move between jobs.
Files are assigned greedily, longest first, to the least-loaded shard, using the
per-file durations stored in ``DURATIONS_FILE``. A file with no stored duration
(a new test file, say) is weighted as the median, so the split stays reasonable
between refreshes of that file.

Set ``CARTOGRAPHY_TEST_SHARD`` to ``<index>/<total>`` (0-based index) to select a
shard. Refresh the stored durations with ``python -m tests.update_shard_durations``.
"""

import json
import os
import statistics
from collections.abc import Iterable
from collections.abc import Mapping
from pathlib import Path

SHARD_ENV_VAR = "CARTOGRAPHY_TEST_SHARD"
DURATIONS_FILE = Path(__file__).parent / "shard_durations.json"


def parse_shard(value: str) -> tuple[int, int]:
    """Parse ``"<index>/<total>"`` into a 0-based index and a shard count."""
    try:
        index_text, total_text = value.split("/")
        index, total = int(index_text), int(total_text)
    except ValueError:
        raise ValueError(
            f"{SHARD_ENV_VAR} must look like '<index>/<total>', got {value!r}",
        ) from None
    if total < 1 or not 0 <= index < total:
        raise ValueError(
            f"{SHARD_ENV_VAR} index must be in [0, total), got {value!r}",
        )
    return index, total


def assign_shards(
    files: Iterable[str],
    durations: Mapping[str, float],
    total: int,
) -> dict[str, int]:
    """Map each file to a shard index, balancing the stored durations."""
    unique_files = sorted(set(files))
    known = [durations[f] for f in unique_files if f in durations]
    default = statistics.median(known) if known else 1.0
    weighted = sorted(
        ((durations.get(f, default), f) for f in unique_files),
        # Longest first; ties broken by path so every job computes the same split.
        key=lambda pair: (-pair[0], pair[1]),
    )
    loads = [0.0] * total
    assignment: dict[str, int] = {}
    for weight, path in weighted:
        shard = min(range(total), key=lambda i: (loads[i], i))
        assignment[path] = shard
        loads[shard] += weight
    return assignment


def load_durations(path: Path = DURATIONS_FILE) -> dict[str, float]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def selected_shard() -> tuple[int, int] | None:
    value = os.environ.get(SHARD_ENV_VAR)
    if not value:
        return None
    return parse_shard(value)
