import copy
import io
from datetime import datetime
from datetime import timezone
from unittest.mock import patch

import pytest
import requests

import cartography.intel.cve_metadata
from cartography.config import Config
from cartography.intel.cve_metadata import CVE_METADATA_FEED_ID
from cartography.intel.cve_metadata import get_cve_ids_from_graph
from cartography.intel.cve_metadata import start_cve_metadata_ingestion
from cartography.intel.cve_metadata.nvd import transform_cves
from cartography.intel.cve_metadata.vulnrichment import read_vulnrichment_archive
from cartography.util import run_analysis_job
from tests.data.cve_metadata.kev import GET_KEV_CATALOG
from tests.data.cve_metadata.nvd import GET_NVD_API_DATA
from tests.data.cve_metadata.vulnrichment import ARCHIVE_RECORDS
from tests.data.cve_metadata.vulnrichment import build_vulnrichment_archive
from tests.data.cve_metadata.vulnrichment import VULNRICHMENT_COMMIT
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 987654321


@pytest.fixture(autouse=True)
def _clear_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


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


def _mock_kev(http_session):
    return copy.deepcopy(GET_KEV_CATALOG)


def _mock_vulnrichment(http_session, cve_ids):
    archive = build_vulnrichment_archive(ARCHIVE_RECORDS)
    return read_vulnrichment_archive(io.BytesIO(archive), cve_ids)


def _mock_truncated_vulnrichment(http_session, cve_ids):
    archive = build_vulnrichment_archive(ARCHIVE_RECORDS)
    return read_vulnrichment_archive(io.BytesIO(archive[: len(archive) // 2]), cve_ids)


def test_get_cve_ids_from_graph(neo4j_session):
    _create_cve_nodes(neo4j_session)
    neo4j_session.run(
        """
        CREATE (:CVE {
            id: 'CVE-2024-0001',
            cve_id: 'CVE-2024-0001',
            _module_name: 'cartography:cve'
        })
        CREATE (:CVE:Vulnerability {
            id: 'CVE-2024-0002',
            cve_id: 'CVE-2024-0002',
            _module_name: 'cartography:cve'
        })
        CREATE (preserved:CVE {
            id: 'CVE-2024-0003',
            cve_id: 'CVE-2024-0003',
            _module_name: 'cartography:cve'
        })
        CREATE (finding:Finding {id: 'finding'})
        CREATE (finding)-[:AFFECTS]->(preserved)
        """,
    )
    cve_ids = get_cve_ids_from_graph(neo4j_session)
    assert set(cve_ids) == {
        "CVE-2023-41782",
        "CVE-2024-0002",
        "CVE-2024-0003",
        "CVE-2024-22075",
    }


def test_deprecated_cve_feed_cleanup(neo4j_session):
    neo4j_session.run(
        """
        CREATE (deleted:CVE {
            id: 'CVE-2024-0001',
            cve_id: 'CVE-2024-0001',
            _module_name: 'cartography:cve'
        })
        CREATE (preserved:CVE {
            id: 'CVE-2024-0002',
            cve_id: 'CVE-2024-0002',
            _module_name: 'cartography:cve'
        })
        CREATE (feed:Feed {id: 'feed'})
        CREATE (metadata:CVEMetadata {id: 'CVE-2024-0001'})
        CREATE (finding:Finding {id: 'finding'})
        CREATE (feed)-[:RESOURCE]->(deleted)
        CREATE (metadata)-[:ENRICHES]->(deleted)
        CREATE (feed)-[:RESOURCE]->(preserved)
        CREATE (finding)-[:AFFECTS]->(preserved)
        """,
    )

    run_analysis_job(
        "cve_deprecated_feed_cleanup.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_nodes(neo4j_session, "CVE", ["cve_id"]) == {("CVE-2024-0002",)}


@patch.object(
    cartography.intel.cve_metadata.vulnrichment,
    "get_vulnrichment_records",
    side_effect=_mock_vulnrichment,
)
@patch.object(
    cartography.intel.cve_metadata.kev,
    "get_kev_catalog",
    side_effect=_mock_kev,
)
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
def test_sync(mock_nvd, mock_epss, mock_kev, mock_vulnrichment, neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session)
    # A finding node carrying the :CVE semantic label should also be enriched by
    # CVEMetadata, not just the deprecated standalone CVE node (issue #3049).
    neo4j_session.run(
        """
        CREATE (:AWSInspectorFinding:CVE {
            id: 'inspector-finding-1',
            cve_id: 'CVE-2023-41782',
            lastupdated: $update_tag
        })
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - Run full sync entrypoint
    start_cve_metadata_ingestion(neo4j_session, config)

    # Assert - CVEMetadataFeed node exists with source flags and source versions
    assert check_nodes(
        neo4j_session,
        "CVEMetadataFeed",
        [
            "id",
            "source_nvd",
            "source_epss",
            "source_kev",
            "source_vulnrichment",
            "kev_catalog_version",
            "kev_date_released",
            "vulnrichment_commit",
        ],
    ) == {
        (
            CVE_METADATA_FEED_ID,
            True,
            True,
            True,
            True,
            "2024.01.10",
            datetime(2024, 1, 10, 15, 0, 0, 10500, tzinfo=timezone.utc),
            VULNRICHMENT_COMMIT,
        ),
    }

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

    # Assert - effect_tags derived (both test CVEs have uninformative/absent CWEs
    # and no HIGH CVSS impacts, so they resolve to the "none" source)
    effect_nodes = check_nodes(
        neo4j_session,
        "CVEMetadata",
        ["id", "effect_tags_source"],
    )
    assert effect_nodes == {
        ("CVE-2023-41782", "none"),
        ("CVE-2024-22075", "none"),
    }

    # Assert - NVD's copy of the KEV data is kept as NVD reports it
    assert check_nodes(
        neo4j_session,
        "CVEMetadata",
        ["id", "cisa_exploit_add", "cisa_action_due"],
    ) == {
        ("CVE-2023-41782", None, None),
        ("CVE-2024-22075", "2024-01-08", "2024-01-29"),
    }

    # Assert - is_kev follows the KEV catalog, which disagrees with NVD on both CVEs
    assert check_nodes(
        neo4j_session,
        "CVEMetadata",
        [
            "id",
            "is_kev",
            "is_kev_source",
            "kev_date_added",
            "kev_due_date",
            "kev_ransomware_use",
            "kev_forensic_triage",
        ],
    ) == {
        ("CVE-2023-41782", True, "kev", "2024-01-09", "2024-01-30", "Known", True),
        ("CVE-2024-22075", False, "kev", None, None, None, None),
    }

    # Assert - the SSVC fields follow Vulnrichment. CVE-2024-22075 has a CNA-only
    # record there, so it has no SSVC decision but does have an update time.
    assert check_nodes(
        neo4j_session,
        "CVEMetadata",
        [
            "id",
            "ssvc_exploitation",
            "ssvc_automatable",
            "ssvc_technical_impact",
            "ssvc_version",
            "ssvc_timestamp",
            "vulnrichment_updated_at",
        ],
    ) == {
        (
            "CVE-2023-41782",
            "active",
            "yes",
            "total",
            "2.0.3",
            datetime(2024, 8, 1, 19, 28, 25, 242481, tzinfo=timezone.utc),
            datetime(2024, 10, 29, 14, 7, 56, 381000, tzinfo=timezone.utc),
        ),
        (
            "CVE-2024-22075",
            None,
            None,
            None,
            None,
            None,
            datetime(2024, 5, 28, 18, 59, 27, 726000, tzinfo=timezone.utc),
        ),
    }

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

    # Assert - ENRICHES also reaches finding nodes carrying the :CVE label
    assert check_rels(
        neo4j_session,
        "CVEMetadata",
        "id",
        "AWSInspectorFinding",
        "id",
        "ENRICHES",
    ) == {
        ("CVE-2023-41782", "inspector-finding-1"),
    }


@patch.object(
    cartography.intel.cve_metadata.vulnrichment,
    "get_vulnrichment_records",
    side_effect=_mock_vulnrichment,
)
@patch.object(
    cartography.intel.cve_metadata.kev,
    "get_kev_catalog",
    side_effect=_mock_kev,
)
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
def test_cleanup_removes_stale_metadata(
    mock_nvd,
    mock_epss,
    mock_kev,
    mock_vulnrichment,
    neo4j_session,
):
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


@pytest.mark.parametrize(
    "sources, expected",
    [
        # NVD's copy of the KEV data fills in for the catalog.
        (
            ["nvd", "kev"],
            {("CVE-2023-41782", False, "nvd"), ("CVE-2024-22075", True, "nvd")},
        ),
        # Without NVD there is no answer, so is_kev stays unset.
        (
            ["kev"],
            {("CVE-2023-41782", None, None), ("CVE-2024-22075", None, None)},
        ),
    ],
    ids=["nvd-fallback", "no-fallback"],
)
@patch.object(
    cartography.intel.cve_metadata.kev,
    "get_kev_catalog",
    side_effect=requests.exceptions.ConnectionError("catalog unreachable"),
)
@patch.object(
    cartography.intel.cve_metadata.nvd,
    "get_and_transform_nvd_cves",
    side_effect=_mock_nvd,
)
def test_sync_kev_fetch_failure(mock_nvd, mock_kev, sources, expected, neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session)
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        cve_metadata_src=sources,
    )

    # Act
    start_cve_metadata_ingestion(neo4j_session, config)

    # Assert
    assert (
        check_nodes(neo4j_session, "CVEMetadata", ["id", "is_kev", "is_kev_source"])
        == expected
    )
    assert check_nodes(
        neo4j_session,
        "CVEMetadataFeed",
        ["source_kev", "kev_catalog_version"],
    ) == {(True, None)}


def _sync_vulnrichment_only(neo4j_session, update_tag, fetch):
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        cve_metadata_src=["vulnrichment"],
    )
    with patch.object(
        cartography.intel.cve_metadata.vulnrichment,
        "get_vulnrichment_records",
        side_effect=fetch,
    ):
        start_cve_metadata_ingestion(neo4j_session, config)


def test_sync_vulnrichment_truncated_archive(neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session)

    # Act - a first sync reads the full archive.
    _sync_vulnrichment_only(neo4j_session, TEST_UPDATE_TAG, _mock_vulnrichment)

    # Assert
    assert ("CVE-2023-41782", "active") in check_nodes(
        neo4j_session,
        "CVEMetadata",
        ["id", "ssvc_exploitation"],
    )

    # Act - the second sync's download is cut short.
    _sync_vulnrichment_only(
        neo4j_session,
        TEST_UPDATE_TAG_2,
        _mock_truncated_vulnrichment,
    )

    # Assert - nothing from the partial archive is written, and the feed node
    # shows that no archive was read.
    assert check_nodes(
        neo4j_session,
        "CVEMetadata",
        ["id", "ssvc_exploitation", "vulnrichment_updated_at"],
    ) == {("CVE-2023-41782", None, None), ("CVE-2024-22075", None, None)}
    assert check_nodes(
        neo4j_session,
        "CVEMetadataFeed",
        ["source_vulnrichment", "vulnrichment_commit"],
    ) == {(True, None)}
