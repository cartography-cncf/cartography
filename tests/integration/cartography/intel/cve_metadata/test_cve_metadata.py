import copy

from cartography.intel.cve_metadata import CVE_METADATA_FEED_ID
from cartography.intel.cve_metadata import get_cve_ids_from_graph
from cartography.intel.cve_metadata import load_cve_metadata
from cartography.intel.cve_metadata import load_cve_metadata_feed
from cartography.intel.cve_metadata.epss import merge_epss_into_cves
from cartography.intel.cve_metadata.nvd import merge_nvd_into_cves
from cartography.intel.cve_metadata.nvd import transform_cves
from tests.data.cve_metadata.nvd import GET_NVD_API_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _create_cve_nodes(neo4j_session):
    neo4j_session.run(
        """
        UNWIND $cve_ids AS cve_id
        MERGE (c:CVE{id: cve_id})
        ON CREATE SET c.firstseen = timestamp(), c.cve_id = cve_id
        """,
        cve_ids=["CVE-2023-41782", "CVE-2024-22075"],
    )


def test_get_cve_ids_from_graph(neo4j_session):
    _create_cve_nodes(neo4j_session)
    cve_ids = get_cve_ids_from_graph(neo4j_session)
    assert set(cve_ids) == {"CVE-2023-41782", "CVE-2024-22075"}


def test_sync(neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session)
    cve_ids = ["CVE-2023-41782", "CVE-2024-22075"]

    # Act - Start from graph CVE IDs (authoritative list)
    cves = [{"id": cve_id} for cve_id in cve_ids]

    # Act - Enrich with NVD data
    nvd_data = transform_cves(copy.deepcopy(GET_NVD_API_DATA), set(cve_ids))
    merge_nvd_into_cves(cves, nvd_data)

    # Act - Enrich with EPSS data
    epss_data = {
        "CVE-2023-41782": {"epss_score": 0.00043, "epss_percentile": 0.08931},
        "CVE-2024-22075": {"epss_score": 0.97530, "epss_percentile": 0.99940},
    }
    merge_epss_into_cves(cves, epss_data)

    # Act - Load via module functions
    load_cve_metadata_feed(neo4j_session, TEST_UPDATE_TAG, {"nvd", "epss"})
    load_cve_metadata(neo4j_session, cves, TEST_UPDATE_TAG)

    # Assert - CVEMetadataFeed node exists
    assert check_nodes(
        neo4j_session,
        "CVEMetadataFeed",
        ["id"],
    ) == {(CVE_METADATA_FEED_ID,)}

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
        ["id", "cisa_exploit_add", "cisa_action_due"],
    )
    assert ("CVE-2024-22075", "2024-01-08", "2024-01-29") in kev_nodes
    # Non-KEV CVE should have None for KEV fields
    assert ("CVE-2023-41782", None, None) in kev_nodes

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
