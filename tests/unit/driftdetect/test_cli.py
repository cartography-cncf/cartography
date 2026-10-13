from unittest.mock import patch

from cartography.driftdetect.cli import CLI
from cartography.driftdetect.config import UpdateConfig
from cartography.driftdetect.util import valid_directory
from tests.integration import settings


def test_valid_directory():
    """
    Tests valid directory function.
    """
    config = UpdateConfig("tests", "localhost")
    assert valid_directory(config.drift_detection_directory)
    config.drift_detection_directory = "temp"
    assert not valid_directory(config.drift_detection_directory)


@patch("cartography.driftdetect.cli.run_get_states")
def test_cli_main(mock_run):
    """
    Tests that CLI runs update.
    """
    cli = CLI(prog="cartography-detectdrift")
    cli.main(
        [
            "get-state",
            "--neo4j-uri",
            settings.get("NEO4J_URL"),
            "--drift-detection-directory",
            "tests/data/test_update_detectors",
        ],
    )
    mock_run.assert_called_once()


def test_configure():
    """
    Tests that the configure method correctly parses args.
    """
    cli = CLI(prog="cartography-detectdrift")
    config = cli.configure(
        [
            "get-state",
            "--neo4j-uri",
            settings.get("NEO4J_URL"),
            "--drift-detection-directory",
            "tests/data/detectors",
        ],
    )
    assert config.drift_detection_directory == "tests/data/detectors"
    assert config.neo4j_uri == settings.get("NEO4J_URL")
