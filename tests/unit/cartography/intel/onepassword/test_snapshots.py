import copy
import json

import pytest

from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.onepassword import snapshots
from tests.data.onepassword import snapshots as data


def _get(tmp_path, documents):
    for name, document in documents.items():
        (tmp_path / name).write_text(json.dumps(document))
    with LocalReportReader(str(tmp_path)) as reader:
        return snapshots.get(reader)


def _with(**changes):
    snapshot = copy.deepcopy(data.SNAPSHOT)
    snapshot.update(changes)
    return snapshot


@pytest.mark.parametrize(
    ("document", "message"),
    [
        (_with(status="partial"), "is not a complete snapshot"),
        (_with(schema_version="2.0"), "unsupported snapshot schema version 2.0"),
        (_with(provider="lastpass"), "is not a 1Password collector snapshot"),
        (["not", "a", "snapshot"], "is not a 1Password collector snapshot"),
    ],
)
def test_get_rejects_snapshots_that_cannot_be_trusted(tmp_path, document, message):
    # Act and assert
    with pytest.raises(ValueError, match=message):
        _get(tmp_path, {"newest.json": data.newer_snapshot(), "bad.json": document})


def test_get_requires_a_snapshot(tmp_path):
    # Arrange
    (tmp_path / "notes.txt").write_text("not a snapshot")

    # Act and assert
    with pytest.raises(ValueError, match="No 1Password snapshots found"):
        _get(tmp_path, {})


def test_get_accepts_minor_schema_versions(tmp_path):
    # Act
    result = _get(tmp_path, {"snapshot.json": _with(schema_version="1.1")})

    # Assert
    assert [snapshot["schema_version"] for snapshot in result] == ["1.1"]


def test_get_breaks_collection_time_ties_deterministically(tmp_path):
    # Arrange
    later_id = _with(snapshot_id="ffffffff-ffff-4fff-8fff-ffffffffffff")

    # Act
    result = _get(tmp_path, {"a.json": later_id, "b.json": data.SNAPSHOT})

    # Assert
    assert [snapshot["snapshot_id"] for snapshot in result] == [later_id["snapshot_id"]]
