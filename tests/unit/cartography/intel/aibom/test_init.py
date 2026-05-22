import copy
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.aibom import _extract_digest_from_source_key
from cartography.intel.aibom import _image_digest_exists
from cartography.intel.aibom import prepare_aibom_report_for_ingestion
from tests.data.aibom.aibom_sample import AIBOM_REPORT
from tests.data.aibom.aibom_sample import TEST_SOURCE_KEY


def test_extract_digest_from_source_key_returns_digest() -> None:
    # Arrange
    expected_digest = (
        "sha256:914758fa1c15b12c7dfa8cab15eb53b7bbb5143386911da492b00c73c49eef6f"
    )

    # Act
    digest = _extract_digest_from_source_key(TEST_SOURCE_KEY)

    # Assert
    assert digest == expected_digest


def test_image_digest_exists_returns_true_when_image_node_exists() -> None:
    # Arrange
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = "sha256:test"

    # Act
    result = _image_digest_exists(neo4j_session, "sha256:test")

    # Assert
    assert result is True
    neo4j_session.execute_read.assert_called_once()
    execute_read_args = neo4j_session.execute_read.call_args
    assert (
        execute_read_args.args[1]
        == "MATCH (img:Image {_ont_digest: $digest}) RETURN img._ont_digest LIMIT 1"
    )
    assert execute_read_args.kwargs == {"digest": "sha256:test"}


def test_image_digest_exists_returns_false_when_image_node_missing() -> None:
    # Arrange
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = None

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


def test_prepare_aibom_report_for_ingestion_raises_when_image_digest_missing() -> None:
    # Arrange
    neo4j_session = MagicMock()
    document = copy.deepcopy(AIBOM_REPORT)

    with patch("cartography.intel.aibom._image_digest_exists", return_value=False):
        # Act and assert
        with pytest.raises(ValueError):
            prepare_aibom_report_for_ingestion(
                neo4j_session,
                document,
                "/tmp/aibom.json",
            )


def test_prepare_aibom_report_for_ingestion_raises_for_mixed_digest_and_non_digest_source_keys() -> (
    None
):
    # Arrange
    neo4j_session = MagicMock()
    document: dict[str, Any] = copy.deepcopy(AIBOM_REPORT)
    document["aibom_analysis"]["sources"]["repo:latest"] = copy.deepcopy(
        document["aibom_analysis"]["sources"][TEST_SOURCE_KEY],
    )

    # Act and assert
    with pytest.raises(
        ValueError,
        match="contained non-digest-qualified source keys: repo:latest",
    ):
        prepare_aibom_report_for_ingestion(
            neo4j_session,
            document,
            "/tmp/aibom.json",
        )


def test_prepare_aibom_report_for_ingestion_raises_when_sources_are_empty() -> None:
    # Arrange
    neo4j_session = MagicMock()
    document: dict[str, Any] = copy.deepcopy(AIBOM_REPORT)
    document["aibom_analysis"]["sources"] = {}

    # Act and assert
    with pytest.raises(
        ValueError,
        match="did not contain any sources",
    ):
        prepare_aibom_report_for_ingestion(
            neo4j_session,
            document,
            "/tmp/aibom.json",
        )
