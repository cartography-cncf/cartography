import pytest

from cartography.driftdetect.config import GetDriftConfig
from cartography.driftdetect.detect_deviations import perform_drift_detection
from cartography.driftdetect.detect_deviations import run_drift_detection
from cartography.driftdetect.model import State
from cartography.driftdetect.serializers import StateSchema
from cartography.driftdetect.storage import FileSystem


@pytest.mark.parametrize("empty_first", [True, False], ids=["additions", "removals"])
def test_compare_snapshot_without_column_metadata(empty_first):
    # Arrange
    empty = State("exposed", "MATCH (n) RETURN n.id", [], [])
    populated = State("exposed", empty.validation_query, ["n.id"], [["node-1"]])
    start, end = (empty, populated) if empty_first else (populated, empty)

    # Act
    new_results, missing_results = perform_drift_detection(start, end)

    # Assert
    assert new_results == ([["node-1"]] if empty_first else [])
    assert missing_results == ([] if empty_first else [["node-1"]])
    assert empty.properties == []
    assert populated.properties == ["n.id"]


@pytest.mark.parametrize("empty_first", [True, False], ids=["additions", "removals"])
def test_report_snapshot_without_column_metadata(tmp_path, capsys, caplog, empty_first):
    # Arrange
    empty = State("exposed", "MATCH (n) RETURN n.id, n.groups", [], [])
    populated = State(
        "exposed", empty.validation_query, ["n.id", "n.groups"], [["node-1", "a|b"]]
    )
    start, end = (empty, populated) if empty_first else (populated, empty)
    serializer = StateSchema()
    FileSystem.write(serializer.dump(start), tmp_path / "start.json")
    FileSystem.write(serializer.dump(end), tmp_path / "end.json")
    FileSystem.write({"name": "exposed", "shortcuts": {}}, tmp_path / "shortcut.json")
    config = GetDriftConfig(str(tmp_path), "start.json", "end.json")

    # Act
    run_drift_detection(config)

    # Assert
    output = capsys.readouterr().out
    assert ("New Query Results:" if empty_first else "Missing Query Results:") in output
    assert (
        "Missing Query Results:" if empty_first else "New Query Results:"
    ) not in output
    assert "n.id :  node-1" in output
    assert "n.groups :  ['a', 'b']" in output
    assert output.index("n.id") < output.index("n.groups")
    assert not caplog.records
    assert FileSystem.load(tmp_path / "start.json") == serializer.dump(start)
    assert FileSystem.load(tmp_path / "end.json") == serializer.dump(end)


@pytest.mark.parametrize(
    "properties,results",
    [(["other"], []), (["other"], [["node-1"]]), ([], [["node-1"]])],
    ids=["known-empty", "known-populated", "missing-populated"],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_column_mismatches_remain_errors(properties, results, reverse):
    # Arrange
    populated = State("exposed", "MATCH (n) RETURN n.id", ["n.id"], [["node-1"]])
    other = State("exposed", populated.validation_query, properties, results)
    start, end = (other, populated) if reverse else (populated, other)

    # Act and assert
    with pytest.raises(ValueError, match="^State properties do not match\\.$"):
        perform_drift_detection(start, end)


@pytest.mark.parametrize(
    "name,query,message",
    [
        ("other", "MATCH (n) RETURN n.id", "State names do not match."),
        ("exposed", "MATCH (n) RETURN n.name", "State queries do not match."),
    ],
)
def test_unknown_columns_do_not_bypass_state_identity(name, query, message):
    # Arrange
    populated = State("exposed", "MATCH (n) RETURN n.id", ["n.id"], [["node-1"]])
    empty = State(name, query, [], [])

    # Act and assert
    with pytest.raises(ValueError, match=message):
        perform_drift_detection(populated, empty)


@pytest.mark.parametrize("properties", [[], ["n.id"]])
def test_empty_snapshots_have_no_drift(properties):
    # Arrange
    start = State("exposed", "MATCH (n) RETURN n.id", [], [])
    end = State("exposed", start.validation_query, properties, [])

    # Act
    result = perform_drift_detection(start, end)

    # Assert
    assert result == ([], [])
