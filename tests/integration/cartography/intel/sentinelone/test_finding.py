from unittest.mock import patch

import cartography.intel.sentinelone.finding
from tests.data.sentinelone.finding import CVE_ID_1
from tests.data.sentinelone.finding import CVE_ID_2
from tests.data.sentinelone.finding import CVE_ID_3
from tests.data.sentinelone.finding import CVES_DATA
from tests.data.sentinelone.finding import TEST_ACCOUNT_ID
from tests.data.sentinelone.finding import TEST_COMMON_JOB_PARAMETERS
from tests.data.sentinelone.finding import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

# Expected application version IDs based on the test data
EXPECTED_APP_VERSION_IDS = {
    CVE_ID_1: "openssl_foundation:openssl:1.1.1k",
    CVE_ID_2: "apache_software_foundation:apache_http_server:2.4.41",
    CVE_ID_3: "nodejs_foundation:nodejs:16.14.2",
}

# Expected Agent IDs based on the test data
EXPECTED_AGENT_IDS = {
    CVE_ID_1: "agent-123",
    CVE_ID_2: "agent-456",
    CVE_ID_3: "agent-789",
}


@patch.object(
    cartography.intel.sentinelone.finding,
    "get_paginated_results",
)
def test_sync_cves(mock_get_paginated_results, neo4j_session):
    """
    Test that AppFinding sync works properly by syncing AppFindings and verifying nodes and relationships
    including relationships between S1AppFinding, S1ApplicationVersion and S1Agent
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

    # Create prerequisite S1Agent nodes for the relationships
    for agent_id in EXPECTED_AGENT_IDS.values():
        neo4j_session.run(
            "CREATE (ag:S1Agent {id: $agent_id, lastupdated: $update_tag})",
            agent_id=agent_id,
            update_tag=TEST_UPDATE_TAG,
        )

    # A finding synced before the :CVE label moved to S1Vulnerability.
    neo4j_session.run(
        """
        MATCH (a:S1Account {id: $account_id})
        MERGE (a)-[:RESOURCE]->(f:S1AppFinding:CVE {id: $id})
        SET f._ont_source = 'sentinelone', f._ont_cve_id = 'CVE-2023-1234',
            f._ont_base_severity = 'high'
        MERGE (:CVEMetadata {id: 'CVE-2023-1234'})-[:ENRICHES]->(f)
        """,
        account_id=TEST_ACCOUNT_ID,
        id=CVE_ID_1,
    )

    # Create prerequisite CVE nodes for the relationships
    for cve in CVES_DATA:
        neo4j_session.run(
            "CREATE (c:CVE {id: $cve_id, lastupdated: $update_tag})",
            cve_id=cve["cveId"],
            update_tag=TEST_UPDATE_TAG,
        )

    # Act: Run the sync
    cartography.intel.sentinelone.finding.sync(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Assert:
    # Verify that the correct AppFinding nodes were created
    expected_nodes = {
        (
            CVE_ID_1,
            "CVE-2023-1234",
            45,
            "2023-11-01T10:00:00Z",
            "2023-12-15T14:30:00Z",
            "vulnerable",
            "active",
        ),
        (
            CVE_ID_2,
            "CVE-2023-5678",
            12,
            "2023-12-01T08:45:00Z",
            "2023-12-15T16:20:00Z",
            "vulnerable",
            "active",
        ),
        (
            CVE_ID_3,
            "CVE-2023-9012",
            90,
            "2023-09-15T12:00:00Z",
            "2023-12-15T09:15:00Z",
            "patched",
            "resolved",
        ),
    }

    actual_nodes = check_nodes(
        neo4j_session,
        "S1AppFinding",
        [
            "id",
            "cve_id",
            "days_detected",
            "detection_date",
            "last_scan_date",
            "last_scan_result",
            "status",
        ],
    )

    assert actual_nodes == expected_nodes

    # The vulnerability, not each of its findings, is the :CVE node, and it holds
    # the fields SentinelOne reports per CVE.
    assert check_nodes(
        neo4j_session,
        "S1Vulnerability:CVE",
        ["id", "cve_id", "severity", "risk_score", "remediation_level"],
    ) == {
        (
            "S1|test-s1-account-123|CVE-2023-1234",
            "CVE-2023-1234",
            "High",
            8.2,
            "Official Fix",
        ),
        (
            "S1|test-s1-account-123|CVE-2023-5678",
            "CVE-2023-5678",
            "Critical",
            None,
            None,
        ),
        ("S1|test-s1-account-123|CVE-2023-9012", "CVE-2023-9012", "Medium", None, None),
    }
    assert check_rels(
        neo4j_session,
        "S1AppFinding",
        "id",
        "S1Vulnerability",
        "id",
        "HAS_VULNERABILITY",
        rel_direction_right=True,
    ) == {
        (CVE_ID_1, "S1|test-s1-account-123|CVE-2023-1234"),
        (CVE_ID_2, "S1|test-s1-account-123|CVE-2023-5678"),
        (CVE_ID_3, "S1|test-s1-account-123|CVE-2023-9012"),
    }
    assert check_rels(
        neo4j_session,
        "S1Account",
        "id",
        "S1Vulnerability",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "S1|test-s1-account-123|CVE-2023-1234"),
        (TEST_ACCOUNT_ID, "S1|test-s1-account-123|CVE-2023-5678"),
        (TEST_ACCOUNT_ID, "S1|test-s1-account-123|CVE-2023-9012"),
    }
    # Findings keep their deprecated copies of the per-CVE fields until v1.0.0.
    assert check_nodes(
        neo4j_session, "S1AppFinding", ["id", "severity", "report_confidence"]
    ) == {
        (CVE_ID_1, "High", "Confirmed"),
        (CVE_ID_2, "Critical", None),
        (CVE_ID_3, "Medium", None),
    }
    # The sync strips :CVE and its ontology fields from the finding stored before
    # the move. CVEMetadata cleanup only reaches :CVE nodes, so the sync also
    # removes the enrichment edge the old label brought.
    assert check_nodes(neo4j_session, "S1AppFinding:CVE", ["id"]) == set()
    assert (
        neo4j_session.run(
            """
            MATCH (f:S1AppFinding)
            RETURN collect(DISTINCT [k IN keys(f) WHERE k STARTS WITH '_ont_']) AS ont
            """,
        ).single()["ont"]
        == [[]]
    )
    assert (
        check_rels(
            neo4j_session,
            "CVEMetadata",
            "id",
            "S1AppFinding",
            "id",
            "ENRICHES",
        )
        == set()
    )

    # Verify that relationships to the account were created
    expected_rels = {
        (CVE_ID_1, TEST_ACCOUNT_ID),
        (CVE_ID_2, TEST_ACCOUNT_ID),
        (CVE_ID_3, TEST_ACCOUNT_ID),
    }

    actual_rels = check_rels(
        neo4j_session,
        "S1AppFinding",
        "id",
        "S1Account",
        "id",
        "RESOURCE",
        rel_direction_right=False,  # (:S1AppFinding)<-[:RESOURCE]-(:S1Account)
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
        "S1AppFinding",
        "id",
        "S1ApplicationVersion",
        "id",
        "AFFECTS",
        rel_direction_right=True,  # (:S1AppFinding)-[:AFFECTS]->(:S1ApplicationVersion)
    )

    assert actual_app_rels == expected_app_rels

    # Verify that relationships to agents were created
    expected_agent_rels = {
        (CVE_ID_1, EXPECTED_AGENT_IDS[CVE_ID_1]),
        (CVE_ID_2, EXPECTED_AGENT_IDS[CVE_ID_2]),
        (CVE_ID_3, EXPECTED_AGENT_IDS[CVE_ID_3]),
    }

    actual_agent_rels = check_rels(
        neo4j_session,
        "S1AppFinding",
        "id",
        "S1Agent",
        "id",
        "AFFECTS",
        rel_direction_right=True,  # (:S1AppFinding)-[:AFFECTS]->(:S1Agent)
    )

    assert actual_agent_rels == expected_agent_rels

    # Verify that relationships to CVEs were created
    expected_cve_rels = {
        (CVE_ID_1, "CVE-2023-1234"),
        (CVE_ID_2, "CVE-2023-5678"),
        (CVE_ID_3, "CVE-2023-9012"),
    }

    actual_cve_rels = check_rels(
        neo4j_session,
        "S1AppFinding",
        "id",
        "CVE",
        "id",
        "LINKED_TO",
        rel_direction_right=True,  # (:S1AppFinding)-[:LINKED_TO]->(:CVE)
    )

    assert actual_cve_rels == expected_cve_rels

    # Verify that the lastupdated field was set correctly
    result = neo4j_session.run(
        "MATCH (c:S1AppFinding) RETURN c.lastupdated as lastupdated LIMIT 1"
    )
    record = result.single()
    assert record["lastupdated"] == TEST_UPDATE_TAG


@patch.object(
    cartography.intel.sentinelone.finding,
    "get_paginated_results",
)
def test_sync_cves_cleanup(mock_get_paginated_results, neo4j_session):
    """
    Test that AppFinding sync properly cleans up stale AppFindings
    """
    # Clean up any existing data from previous tests
    neo4j_session.run("MATCH (c:S1AppFinding) DETACH DELETE c")
    neo4j_session.run("MATCH (a:S1Account) DETACH DELETE a")

    # Create an old AppFinding that should be cleaned up
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (old:S1AppFinding {
            id: 'old-cve-123',
            cve_id: 'CVE-2022-OLD',
            lastupdated: $old_update_tag
        })
        CREATE (acc:S1Account {id: $account_id, lastupdated: $update_tag})
        CREATE (old)<-[:RESOURCE]-(acc)
        """,
        old_update_tag=old_update_tag,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Mock the API call to return only new CVEs
    mock_get_paginated_results.return_value = [CVES_DATA[0]]  # Only first CVE

    # Run the sync
    cartography.intel.sentinelone.finding.sync(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Verify that only the new AppFinding exists
    result = neo4j_session.run("MATCH (c:S1AppFinding) RETURN c.id as id")
    existing_cves = {record["id"] for record in result}

    assert "old-cve-123" not in existing_cves
    assert CVE_ID_1 in existing_cves


@patch.object(
    cartography.intel.sentinelone.finding,
    "get_paginated_results",
)
def test_migration_without_cleanup_strips_only_findings_it_read(
    mock_get_paginated_results, neo4j_session
):
    # Arrange: two findings that an earlier version labeled :CVE. A site-scoped sync
    # skips cleanup and reads only one of them, together with a second finding of
    # the same CVE on another endpoint.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (a:S1Account {id: $account_id})
        CREATE (a)-[:RESOURCE]->(:S1AppFinding:CVE {id: $id, _ont_cve_id: 'CVE-2023-1234'})
        CREATE (a)-[:RESOURCE]->(sibling:S1AppFinding:CVE {id: 'sibling-site-finding', _ont_cve_id: 'CVE-2023-1234'})
        CREATE (:CVEMetadata {id: 'CVE-2023-1234'})-[:ENRICHES]->(sibling)
        """,
        account_id=TEST_ACCOUNT_ID,
        id=CVE_ID_1,
    )
    mock_get_paginated_results.return_value = [
        CVES_DATA[0],
        {
            **CVES_DATA[0],
            "id": "cve-test-123-other-endpoint",
            "endpointId": "agent-456",
        },
    ]

    # Act
    cartography.intel.sentinelone.finding.sync(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
        do_cleanup=False,
    )
    cartography.intel.sentinelone.finding.migrate_legacy_cve_labels(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Assert: both findings of the CVE share one vulnerability node, and the
    # finding the sync did not read keeps :CVE and its enrichment until a sync
    # links it to its vulnerability.
    assert check_rels(
        neo4j_session,
        "S1AppFinding",
        "id",
        "S1Vulnerability",
        "id",
        "HAS_VULNERABILITY",
        rel_direction_right=True,
    ) == {
        (CVE_ID_1, "S1|test-s1-account-123|CVE-2023-1234"),
        ("cve-test-123-other-endpoint", "S1|test-s1-account-123|CVE-2023-1234"),
    }
    assert check_nodes(neo4j_session, "CVE", ["id"]) == {
        ("S1|test-s1-account-123|CVE-2023-1234",),
        ("sibling-site-finding",),
    }
    assert check_rels(
        neo4j_session,
        "CVEMetadata",
        "id",
        "S1AppFinding",
        "id",
        "ENRICHES",
    ) == {("CVE-2023-1234", "sibling-site-finding")}
