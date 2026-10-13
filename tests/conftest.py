import json
import os
from collections import defaultdict
from pathlib import Path

import pytest

from tests import sharding

# Set to a path to record how long each test file took (setup, call and teardown,
# so module-scoped fixtures count too). `python -m tests.update_shard_durations` merges
# these into `tests/shard_durations.json`.
STORE_DURATIONS_ENV_VAR = "CARTOGRAPHY_STORE_SHARD_DURATIONS"

_file_durations: defaultdict[str, float] = defaultdict(float)


def pytest_collection_modifyitems(config, items):
    shard = sharding.selected_shard()
    if shard is None:
        return
    index, total = shard

    def relpath(item):
        return item.path.relative_to(config.rootpath).as_posix()

    assignment = sharding.assign_shards(
        (relpath(item) for item in items),
        sharding.load_durations(),
        total,
    )
    selected = [item for item in items if assignment[relpath(item)] == index]
    deselected = [item for item in items if assignment[relpath(item)] != index]
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


def _is_xdist_worker(config) -> bool:
    return hasattr(config, "workerinput")


def pytest_runtest_logreport(report):
    if os.environ.get(STORE_DURATIONS_ENV_VAR):
        _file_durations[report.location[0]] += report.duration


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    path = os.environ.get(STORE_DURATIONS_ENV_VAR)
    # Under xdist the controller receives every worker's reports, so only it writes.
    if path and _file_durations and not _is_xdist_worker(session.config):
        Path(path).write_text(
            json.dumps(
                {f: round(d, 2) for f, d in sorted(_file_durations.items())},
                indent=2,
            )
            + "\n",
        )
