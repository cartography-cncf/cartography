import pytest

from cartography.driftdetect.detect_deviations import perform_drift_detection
from cartography.driftdetect.serializers import StateSchema
from cartography.driftdetect.storage import FileSystem


def test_basic_drift_detection():
    """
    Tests that drift detection works.
    """
    data = FileSystem.load("tests/data/test_cli_detectors/detector/1.json")
    start_state = StateSchema().load(data)
    data = FileSystem.load("tests/data/test_cli_detectors/detector/2.json")
    end_state = StateSchema().load(data)
    new_results, missing_results = perform_drift_detection(start_state, end_state)
    assert ["36", "37", ["38", "39", "40"]] in new_results
    assert ["7", "14", ["21", "28", "35"]] in missing_results


def test_drift_detection_errors():
    data = FileSystem.load("tests/data/test_cli_detectors/detector/1.json")
    start_state = StateSchema().load(data)
    data = FileSystem.load("tests/data/test_cli_detectors/detector/2.json")
    end_state = StateSchema().load(data)

    start_state.name = "Wrong Name"
    with pytest.raises(ValueError):
        perform_drift_detection(start_state, end_state)

    start_state = StateSchema().load(data)
    start_state.properties = ["Incorrect", "Properties"]
    with pytest.raises(ValueError):
        perform_drift_detection(start_state, end_state)

    start_state = StateSchema().load(data)
    start_state.validation_query = "Invalid Validation Query"
    with pytest.raises(ValueError):
        perform_drift_detection(start_state, end_state)
