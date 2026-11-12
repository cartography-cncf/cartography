import copy
import json

import pytest

from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.common.object_store import ObjectStoreError
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
    ("document", "reason"),
    [
        (_with(status="partial"), snapshots.INCOMPLETE),
        (_with(schema_version="2.0"), snapshots.UNSUPPORTED_VERSION),
        (_with(provider="lastpass"), snapshots.NOT_A_SNAPSHOT),
        (["not", "a", "snapshot"], snapshots.NOT_A_SNAPSHOT),
        (_with(items=None), snapshots.NOT_A_SNAPSHOT),
    ],
)
def test_get_rejects_snapshots_that_cannot_be_trusted(tmp_path, document, reason):
    # Act and assert
    with pytest.raises(snapshots.SnapshotError, match="bad.json") as error:
        _get(tmp_path, {"newest.json": data.newer_snapshot(), "bad.json": document})
    assert error.value.reason == reason


def test_get_requires_a_snapshot(tmp_path):
    # Arrange
    (tmp_path / "notes.txt").write_text("not a snapshot")

    # Act and assert
    with pytest.raises(snapshots.SnapshotError) as error:
        _get(tmp_path, {})
    assert error.value.reason == snapshots.NO_SNAPSHOT


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


def test_get_stops_on_unparseable_json(tmp_path):
    # Arrange
    (tmp_path / "newest.json").write_text(json.dumps(data.newer_snapshot()))
    (tmp_path / "broken.json").write_text("{not json")

    # Act and assert
    with pytest.raises(ObjectStoreError, match="broken.json"):
        with LocalReportReader(str(tmp_path)) as reader:
            snapshots.get(reader)
