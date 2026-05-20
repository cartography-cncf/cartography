import copy
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.aibom import _extract_digest_from_source_key
from cartography.intel.aibom import _image_digest_exists
from cartography.intel.aibom import prepare_aibom_report_for_ingestion
from tests.data.aibom.aibom_sample import AIBOM_REPORT
from tests.data.aibom.aibom_sample import TEST_SOURCE_KEY


def _get_first_source(document: dict[str, Any]) -> dict[str, Any]:
    sources = document["aibom_analysis"]["sources"]
    return next(iter(sources.values()))


def test_extract_digest_from_source_key_returns_digest() -> None:
    # Arrange
    expected_digest = (
        "sha256:914758fa1c15b12c7dfa8cab15eb53b7bbb5143386911da492b00c73c49eef6f"
    )

    # Act
    digest = _extract_digest_from_source_key(TEST_SOURCE_KEY)

    # Assert
    assert digest == expected_digest


def test_extract_digest_from_source_key_returns_none_for_tag_only_source() -> None:
    # Arrange
    source_key = "205930638578.dkr.ecr.us-east-1.amazonaws.com/subimage-backend:latest"

    # Act
    digest = _extract_digest_from_source_key(source_key)

    # Assert
    assert digest is None


def test_image_digest_exists_returns_true_when_image_node_exists() -> None:
    # Arrange
    neo4j_session = MagicMock()
    neo4j_session.run.return_value.single.return_value = {"_ont_digest": "sha256:test"}

    # Act
    result = _image_digest_exists(neo4j_session, "sha256:test")

    # Assert
    assert result is True
    neo4j_session.run.assert_called_once_with(
        "MATCH (img:Image {_ont_digest: $digest}) RETURN img._ont_digest LIMIT 1",
        digest="sha256:test",
    )


def test_image_digest_exists_returns_false_when_image_node_missing() -> None:
    # Arrange
    neo4j_session = MagicMock()
    neo4j_session.run.return_value.single.return_value = None

    # Act
    result = _image_digest_exists(neo4j_session, "sha256:missing")

    # Assert
    assert result is False


def test_prepare_aibom_report_for_ingestion_returns_document_for_exact_image_match() -> (
    None
):
    # Arrange
    neo4j_session = MagicMock()
    document = copy.deepcopy(AIBOM_REPORT)

    with patch("cartography.intel.aibom._image_digest_exists", return_value=True):
        # Act
        prepared_report = prepare_aibom_report_for_ingestion(
            neo4j_session,
            document,
            "/tmp/aibom.json",
        )

    # Assert
    assert prepared_report == document


def test_prepare_aibom_report_for_ingestion_skips_tag_only_source() -> None:
    # Arrange
    document = copy.deepcopy(AIBOM_REPORT)
    source_data = _get_first_source(document)
    # replace source name with a tag only source key (fixtures uses digest)
    source_data["source_name"] = (
        "205930638578.dkr.ecr.us-east-1.amazonaws.com/subimage-backend:latest"
    )
    document["aibom_analysis"]["sources"] = {
        "205930638578.dkr.ecr.us-east-1.amazonaws.com/subimage-backend:latest": source_data,
    }
    neo4j_session = MagicMock()

    # Act
    prepared_report = prepare_aibom_report_for_ingestion(
        neo4j_session,
        document,
        "/tmp/aibom.json",
    )

    # Assert
    assert prepared_report is None


def test_prepare_aibom_report_for_ingestion_skips_when_image_digest_missing() -> None:
    # Arrange
    neo4j_session = MagicMock()
    document = copy.deepcopy(AIBOM_REPORT)

    with patch("cartography.intel.aibom._image_digest_exists", return_value=False):
        # Act
        prepared_report = prepare_aibom_report_for_ingestion(
            neo4j_session,
            document,
            "/tmp/aibom.json",
        )

    # Assert
    assert prepared_report is None
