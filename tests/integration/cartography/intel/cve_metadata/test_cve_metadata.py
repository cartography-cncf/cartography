import copy
from unittest.mock import patch

import cartography.intel.cve_metadata
from cartography.config import Config
from cartography.intel.cve_metadata import CVE_METADATA_FEED_ID
from cartography.intel.cve_metadata import get_cve_ids_from_graph
from cartography.intel.cve_metadata import start_cve_metadata_ingestion
from cartography.intel.cve_metadata.nvd import transform_cves
from tests.data.cve_metadata.nvd import GET_NVD_API_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 987654321


def _create_cve_nodes(neo4j_session, cve_ids=None):
    if cve_ids is None:
        cve_ids = ["CVE-2023-41782", "CVE-2024-22075"]
    neo4j_session.run(
        """
        UNWIND $cve_ids AS cve_id
        MERGE (c:CVE{id: cve_id})
        ON CREATE SET c.firstseen = timestamp(), c.cve_id = cve_id
        """,
        cve_ids=cve_ids,
    )


def _mock_nvd(http_session, cve_ids, api_key=None):
    return transform_cves(copy.deepcopy(GET_NVD_API_DATA), cve_ids)


MOCK_EPSS = {
    "CVE-2023-41782": {"epss_score": 0.00043, "epss_percentile": 0.08931},
    "CVE-2024-22075": {"epss_score": 0.97530, "epss_percentile": 0.99940},
}


def test_get_cve_ids_from_graph(neo4j_session):
    _create_cve_nodes(neo4j_session)
    cve_ids = get_cve_ids_from_graph(neo4j_session)
    assert set(cve_ids) == {"CVE-2023-41782", "CVE-2024-22075"}


@patch.object(
    cartography.intel.cve_metadata.epss,
    "get_epss_scores",
    return_value=MOCK_EPSS,
)
@patch.object(
    cartography.intel.cve_metadata.nvd,
    "get_and_transform_nvd_cves",
    side_effect=_mock_nvd,
)
def test_sync(mock_nvd, mock_epss, neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session)
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - Run full sync entrypoint
    start_cve_metadata_ingestion(neo4j_session, config)

    # Assert - CVEMetadataFeed node exists with source flags
    assert check_nodes(
        neo4j_session,
        "CVEMetadataFeed",
        ["id", "source_nvd", "source_epss"],
    ) == {(CVE_METADATA_FEED_ID, True, True)}

    # Assert - CVEMetadata nodes created with correct properties
    metadata_nodes = check_nodes(
        neo4j_session,
        "CVEMetadata",
        ["id", "base_score", "base_severity", "epss_score", "epss_percentile"],
    )
    assert metadata_nodes == {
        ("CVE-2023-41782", 3.9, "LOW", 0.00043, 0.08931),
        ("CVE-2024-22075", 6.1, "MEDIUM", 0.97530, 0.99940),
    }

    # Assert - CISA KEV fields on the KEV-listed CVE
    kev_nodes = check_nodes(
        neo4j_session,
        "CVEMetadata",
        ["id", "is_kev", "cisa_exploit_add", "cisa_action_due"],
    )
    assert ("CVE-2024-22075", True, "2024-01-08", "2024-01-29") in kev_nodes
    # Non-KEV CVE should have is_kev=False and None for KEV detail fields
    assert ("CVE-2023-41782", False, None, None) in kev_nodes

    # Assert - RESOURCE relationship to feed
    assert check_rels(
        neo4j_session,
        "CVEMetadataFeed",
        "id",
        "CVEMetadata",
        "id",
        "RESOURCE",
    ) == {
        (CVE_METADATA_FEED_ID, "CVE-2023-41782"),
        (CVE_METADATA_FEED_ID, "CVE-2024-22075"),
    }

    # Assert - ENRICHES relationship to CVE
    assert check_rels(
        neo4j_session,
        "CVEMetadata",
        "id",
        "CVE",
        "cve_id",
        "ENRICHES",
    ) == {
        ("CVE-2023-41782", "CVE-2023-41782"),
        ("CVE-2024-22075", "CVE-2024-22075"),
    }


@patch.object(
    cartography.intel.cve_metadata.epss,
    "get_epss_scores",
    return_value=MOCK_EPSS,
)
@patch.object(
    cartography.intel.cve_metadata.nvd,
    "get_and_transform_nvd_cves",
    side_effect=_mock_nvd,
)
def test_cleanup_removes_stale_metadata(mock_nvd, mock_epss, neo4j_session):
    """CVEMetadata nodes for CVEs removed from the graph are cleaned up on the next sync."""
    # Arrange — first sync with 2 CVEs
    _create_cve_nodes(neo4j_session, ["CVE-2023-41782", "CVE-2024-22075"])
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
    )
    start_cve_metadata_ingestion(neo4j_session, config)
    assert len(check_nodes(neo4j_session, "CVEMetadata", ["id"])) == 2

    # Act — remove one CVE from the graph, then run a second sync
    neo4j_session.run("MATCH (c:CVE {id: 'CVE-2024-22075'}) DETACH DELETE c")
    config_2 = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG_2,
    )
    start_cve_metadata_ingestion(neo4j_session, config_2)

    # Assert — only the remaining CVE's metadata survives
    remaining = check_nodes(neo4j_session, "CVEMetadata", ["id"])
    assert remaining == {("CVE-2023-41782",)}
