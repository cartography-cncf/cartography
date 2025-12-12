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

    # Arrange
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

    # Act: Run the sync
    cartography.intel.sentinelone.cve.sync(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Assert:
    # Verify that the correct CVE nodes were created
    expected_nodes = {
        (
            "S1|CVE-2023-1234",
            "CVE-2023-1234",
            7.5,
            "3.1",
            "2023-10-15T00:00:00Z",
            "High",
        ),
        (
            "S1|CVE-2023-5678",
            "CVE-2023-5678",
            9.8,
            "3.1",
            "2023-11-20T00:00:00Z",
            "Critical",
        ),
        (
            "S1|CVE-2023-9012",
            "CVE-2023-9012",
            5.3,
            "3.1",
            "2023-08-30T00:00:00Z",
            "Medium",
        ),
    }

    actual_nodes = check_nodes(
        neo4j_session,
        "S1CVE",
        [
            "id",
            "cve_id",
            "base_score",
            "cvss_version",
            "published_date",
            "severity",
        ],
    )

    assert actual_nodes == expected_nodes

    # Verify that relationships to the account were created
    expected_rels = {
        ("S1|CVE-2023-1234", TEST_ACCOUNT_ID),
        ("S1|CVE-2023-5678", TEST_ACCOUNT_ID),
        ("S1|CVE-2023-9012", TEST_ACCOUNT_ID),
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
        ("S1|CVE-2023-1234", EXPECTED_APP_VERSION_IDS[CVE_ID_1]),
        ("S1|CVE-2023-5678", EXPECTED_APP_VERSION_IDS[CVE_ID_2]),
        ("S1|CVE-2023-9012", EXPECTED_APP_VERSION_IDS[CVE_ID_3]),
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

    # Verify properties on the relationships
    # We query for the properties on the relationship for one of the CVEs
    query = """
    MATCH (c:S1CVE {id: $cve_id})-[r:AFFECTS]->(av:S1ApplicationVersion)
    RETURN r.days_detected as days_detected,
           r.detection_date as detection_date,
           r.last_scan_date as last_scan_date,
           r.last_scan_result as last_scan_result,
           r.status as status
    """

    # Check CVE 1
    result = neo4j_session.run(query, cve_id="S1|CVE-2023-1234")
    record = result.single()
    assert record["days_detected"] == 45
    assert record["detection_date"] == "2023-11-01T10:00:00Z"
    assert record["last_scan_date"] == "2023-12-15T14:30:00Z"
    assert record["last_scan_result"] == "vulnerable"
    assert record["status"] == "active"

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
    assert "S1|CVE-2023-1234" in existing_cves
