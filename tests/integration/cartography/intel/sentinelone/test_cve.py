from unittest.mock import patch

import cartography.intel.sentinelone.cve
from tests.data.sentinelone.cve import CVE_ID_1
from tests.data.sentinelone.cve import CVE_ID_2
from tests.data.sentinelone.cve import CVE_ID_3
from tests.data.sentinelone.cve import CVES_DATA
from tests.data.sentinelone.cve import TEST_ACCOUNT_ID
from tests.data.sentinelone.cve import TEST_COMMON_JOB_PARAMETERS
from tests.data.sentinelone.cve import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

# Expected application version IDs based on the test data
EXPECTED_APP_VERSION_IDS = {
    CVE_ID_1: "openssl_foundation:openssl:1.1.1k",
    CVE_ID_2: "apache_software_foundation:apache_http_server:2.4.41",
    CVE_ID_3: "nodejs_foundation:nodejs:16.14.2",
}


@patch.object(
    cartography.intel.sentinelone.cve,
    "get_paginated_results",
)
def test_sync_cves(mock_get_paginated_results, neo4j_session):
    """
    Test that CVE sync works properly by syncing CVEs and verifying nodes and relationships
    including relationships between S1CVE and S1ApplicationVersion
    """
    # Mock the API call to return test data
    mock_get_paginated_results.return_value = CVES_DATA

    # Create prerequisite account node for the relationship
    neo4j_session.run(
        "CREATE (a:S1Account {id: $account_id, lastupdated: $update_tag})",
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create prerequisite S1ApplicationVersion nodes for the relationships
    for app_version_id in EXPECTED_APP_VERSION_IDS.values():
        neo4j_session.run(
            "CREATE (av:S1ApplicationVersion {id: $app_version_id, lastupdated: $update_tag})",
            app_version_id=app_version_id,
            update_tag=TEST_UPDATE_TAG,
        )

    # Run the sync
    cartography.intel.sentinelone.cve.sync(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Verify that the correct CVE nodes were created
    expected_nodes = {
        (
            CVE_ID_1,
            EXPECTED_APP_VERSION_IDS[CVE_ID_1],
            "CVE-2023-1234",
            7.5,
            "3.1",
            45,
            "2023-11-01T10:00:00Z",
            "2023-12-15T14:30:00Z",
            "vulnerable",
            "2023-10-15T00:00:00Z",
            "High",
            "active",
        ),
        (
            CVE_ID_2,
            EXPECTED_APP_VERSION_IDS[CVE_ID_2],
            "CVE-2023-5678",
            9.8,
            "3.1",
            12,
            "2023-12-01T08:45:00Z",
            "2023-12-15T16:20:00Z",
            "vulnerable",
            "2023-11-20T00:00:00Z",
            "Critical",
            "active",
        ),
        (
            CVE_ID_3,
            EXPECTED_APP_VERSION_IDS[CVE_ID_3],
            "CVE-2023-9012",
            5.3,
            "3.1",
            90,
            "2023-09-15T12:00:00Z",
            "2023-12-15T09:15:00Z",
            "patched",
            "2023-08-30T00:00:00Z",
            "Medium",
            "resolved",
        ),
    }

    actual_nodes = check_nodes(
        neo4j_session,
        "S1CVE",
        [
            "id",
            "application_version_id",
            "cve_id",
            "base_score",
            "cvss_version",
            "days_detected",
            "detection_date",
            "last_scan_date",
            "last_scan_result",
            "published_date",
            "severity",
            "status",
        ],
    )

    assert actual_nodes == expected_nodes

    # Verify that relationships to the account were created
    expected_rels = {
        (CVE_ID_1, TEST_ACCOUNT_ID),
        (CVE_ID_2, TEST_ACCOUNT_ID),
        (CVE_ID_3, TEST_ACCOUNT_ID),
    }

    actual_rels = check_rels(
        neo4j_session,
        "S1CVE",
        "id",
        "S1Account",
        "id",
        "RISK",
        rel_direction_right=False,  # (:S1CVE)<-[:RISK]-(:S1Account)
    )

    assert actual_rels == expected_rels

    # Verify that relationships to application versions were created
    expected_app_rels = {
        (CVE_ID_1, EXPECTED_APP_VERSION_IDS[CVE_ID_1]),
        (CVE_ID_2, EXPECTED_APP_VERSION_IDS[CVE_ID_2]),
        (CVE_ID_3, EXPECTED_APP_VERSION_IDS[CVE_ID_3]),
    }

    actual_app_rels = check_rels(
        neo4j_session,
        "S1CVE",
        "id",
        "S1ApplicationVersion",
        "id",
        "AFFECTS",
        rel_direction_right=True,  # (:S1CVE)-[:AFFECTS]->(:S1ApplicationVersion)
    )

    assert actual_app_rels == expected_app_rels

    # Verify that the lastupdated field was set correctly
    result = neo4j_session.run(
        "MATCH (c:S1CVE) RETURN c.lastupdated as lastupdated LIMIT 1"
    )
    record = result.single()
    assert record["lastupdated"] == TEST_UPDATE_TAG


@patch.object(
    cartography.intel.sentinelone.cve,
    "get_paginated_results",
)
def test_sync_cves_cleanup(mock_get_paginated_results, neo4j_session):
    """
    Test that CVE sync properly cleans up stale CVEs
    """
    # Clean up any existing data from previous tests
    neo4j_session.run("MATCH (c:S1CVE) DETACH DELETE c")
    neo4j_session.run("MATCH (a:S1Account) DETACH DELETE a")

    # Create an old CVE that should be cleaned up
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (old:S1CVE {
            id: 'old-cve-123',
            cve_id: 'CVE-2022-OLD',
            severity: 'High',
            lastupdated: $old_update_tag
        })
        CREATE (acc:S1Account {id: $account_id, lastupdated: $update_tag})
        CREATE (old)<-[:RISK]-(acc)
        """,
        old_update_tag=old_update_tag,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Mock the API call to return only new CVEs
    mock_get_paginated_results.return_value = [CVES_DATA[0]]  # Only first CVE

    # Run the sync
    cartography.intel.sentinelone.cve.sync(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Verify that only the new CVE exists
    result = neo4j_session.run("MATCH (c:S1CVE) RETURN c.id as id")
    existing_cves = {record["id"] for record in result}

    assert "old-cve-123" not in existing_cves
    assert CVE_ID_1 in existing_cves
