import json
import os
import time
from collections import defaultdict
from pathlib import Path

import pytest

from tests import sharding

# Set to a path to record how long each test file took (setup, call and teardown,
# so module-scoped fixtures count too). `python -m tests.update_shard_durations` merges
# these into `tests/shard_durations.json`.
STORE_DURATIONS_ENV_VAR = "CARTOGRAPHY_STORE_SHARD_DURATIONS"

_file_durations: defaultdict[str, float] = defaultdict(float)


_shard_assignment_key = pytest.StashKey[dict[str, int]]()


def _shard_assignment(config, total: int) -> dict[str, int]:
    """Assign every test file under the paths pytest was given to a shard.

    Built from the file system, not from collected items, so files outside the shard
    are skipped before they are imported: collecting the whole integration suite in
    every shard would cost each one the full import time.
    """
    if _shard_assignment_key not in config.stash:
        files: set[str] = set()
        for arg in config.args:
            path = config.invocation_params.dir / arg.split("::")[0]
            if path.is_dir():
                # pytest's default `python_files` patterns, which this repo uses.
                candidates = [*path.rglob("test_*.py"), *path.rglob("*_test.py")]
            else:
                candidates = [path]
            files.update(
                c.resolve().relative_to(config.rootpath).as_posix() for c in candidates
            )
        config.stash[_shard_assignment_key] = sharding.assign_shards(
            files,
            sharding.load_durations(),
            total,
        )
    return config.stash[_shard_assignment_key]


def pytest_ignore_collect(collection_path, config):
    shard = sharding.selected_shard()
    if shard is None or not collection_path.is_file():
        return None
    index, total = shard
    relpath = collection_path.resolve().relative_to(config.rootpath).as_posix()
    assigned = _shard_assignment(config, total).get(relpath)
    if assigned is not None and assigned != index:
        return True
    return None


def pytest_report_header(config):
    shard = sharding.selected_shard()
    if shard is None:
        return None
    index, total = shard
    assignment = _shard_assignment(config, total)
    mine = sum(1 for assigned in assignment.values() if assigned == index)
    return f"shard {index}/{total}: {mine} of {len(assignment)} test files"


def _is_xdist_worker(config) -> bool:
    return hasattr(config, "workerinput")


# Seconds spent setting up session-scoped fixtures (the Neo4j container, say) during
# each file's tests. That cost lands in whichever file happens to run first, and it is
# paid once per job wherever it lands, so it must not count towards that file's weight.
_session_setup_by_file: defaultdict[str, float] = defaultdict(float)
_current_file: str | None = None


def pytest_runtest_logstart(nodeid, location):
    global _current_file
    _current_file = Path(location[0]).as_posix()


class _SessionFixtureTimer:
    # Registered as a plugin rather than defined here as a conftest hook: conftest hooks
    # only see nodes under their directory, and session fixtures run on the Session node.
    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef, request):
        start = time.perf_counter()
        yield
        if fixturedef.scope == "session" and _current_file is not None:
            _session_setup_by_file[_current_file] += time.perf_counter() - start


def pytest_configure(config):
    if os.environ.get(STORE_DURATIONS_ENV_VAR):
        config.pluginmanager.register(_SessionFixtureTimer(), "session-fixture-timer")


def pytest_runtest_logreport(report):
    if os.environ.get(STORE_DURATIONS_ENV_VAR):
        _file_durations[Path(report.location[0]).as_posix()] += report.duration


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    path = os.environ.get(STORE_DURATIONS_ENV_VAR)
    # Under xdist the controller receives every worker's reports, so only it writes.
    if path and _file_durations and not _is_xdist_worker(session.config):
        Path(path).write_text(
            json.dumps(
                {
                    f: round(max(d - _session_setup_by_file[f], 0.0), 2)
                    for f, d in sorted(_file_durations.items())
                },
                indent=2,
            )
            + "\n",
        )
