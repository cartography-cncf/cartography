import pytest

import cartography.intel.wiz
from cartography.config import Config
from tests.data.wiz import AUTH_URL
from tests.data.wiz import CLIENT_ID
from tests.data.wiz import CLIENT_SECRET
from tests.data.wiz import CONFIGURATION_FINDING_ID_1
from tests.data.wiz import CVE_ID_1
from tests.data.wiz import DETECTION_ID_1
from tests.data.wiz import FINDINGS
from tests.data.wiz import GRAPHQL_URL
from tests.data.wiz import ISSUE_ID_1
from tests.data.wiz import ISSUES
from tests.data.wiz import NON_CVE_VULNERABILITY_ID
from tests.data.wiz import RESOURCE_ID_1
from tests.data.wiz import TENANT_ID
from tests.data.wiz import VULNERABILITY_ID_1
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.fixture(autouse=True)
def cleanup_wiz_test_data(neo4j_session):
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:WizTenant
           OR n:WizIssue
           OR n:WizFinding
        DETACH DELETE n
        """,
    )
    neo4j_session.run("MATCH (n:CVE {id: $id}) DETACH DELETE n", id=CVE_ID_1)
    yield
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:WizTenant
           OR n:WizIssue
           OR n:WizFinding
        DETACH DELETE n
        """,
    )
    neo4j_session.run("MATCH (n:CVE {id: $id}) DETACH DELETE n", id=CVE_ID_1)


def _config(
    update_tag: int = TEST_UPDATE_TAG,
    lookback_days: int | None = None,
    project_ids: list[str] | None = None,
) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        wiz_graphql_url=GRAPHQL_URL,
        wiz_auth_url=AUTH_URL,
        wiz_client_id=CLIENT_ID,
        wiz_client_secret=CLIENT_SECRET,
        wiz_tenant_id=TENANT_ID,
        wiz_lookback_days=lookback_days,
        wiz_project_ids=project_ids,
    )


def _seed_cve(neo4j_session):
    neo4j_session.run(
        """
        MERGE (c:CVE {id: $id})
        SET c.lastupdated = $update_tag
        """,
        id=CVE_ID_1,
        update_tag=TEST_UPDATE_TAG,
    )


def _patch_wiz_api(mocker, issues=ISSUES, findings=FINDINGS):
    mocker.patch("cartography.intel.wiz.get_access_token", return_value="token-1")
    mocker.patch("cartography.intel.wiz.issues.get", return_value=issues)
    mocker.patch("cartography.intel.wiz.findings.get", return_value=findings)


def test_start_wiz_ingestion_loads_nodes_and_relationships(neo4j_session, mocker):
    # Arrange
    _seed_cve(neo4j_session)
    _patch_wiz_api(mocker)

    # Act
    cartography.intel.wiz.start_wiz_ingestion(neo4j_session, _config())

    # Assert
    assert check_nodes(neo4j_session, "WizTenant", ["id"]) == {(TENANT_ID,)}
    assert check_nodes(
        neo4j_session,
        "WizIssue",
        ["id", "severity", "status", "resource_id"],
    ) == {
        (ISSUE_ID_1, "HIGH", "OPEN", RESOURCE_ID_1),
    }
    assert check_nodes(
        neo4j_session,
        "WizFinding",
        ["id", "finding_type", "cve_id", "resource_id"],
    ) == {
        (VULNERABILITY_ID_1, "VULNERABILITY", CVE_ID_1, RESOURCE_ID_1),
        (NON_CVE_VULNERABILITY_ID, "VULNERABILITY", None, RESOURCE_ID_1),
        (CONFIGURATION_FINDING_ID_1, "CONFIGURATION", None, "wiz-resource-config-1"),
        (DETECTION_ID_1, "DETECTION", None, "wiz-detection-resource-1"),
    }
    assert check_nodes(
        neo4j_session,
        "SecurityIssue",
        [
            "id",
            "_ont_title",
            "_ont_severity",
            "_ont_status",
            "_ont_type",
            "_ont_first_seen",
            "_ont_source",
        ],
    ) == {
        (
            ISSUE_ID_1,
            "Public VM",
            "high",
            "open",
            "CLOUD_CONFIGURATION",
            "2026-01-03T00:00:00Z",
            "wiz",
        ),
        (
            NON_CVE_VULNERABILITY_ID,
            "openssl advisory",
            "medium",
            "open",
            "VULNERABILITY",
            "2026-01-06T00:00:00Z",
            "wiz",
        ),
        (
            CONFIGURATION_FINDING_ID_1,
            "S3 bucket is public",
            "critical",
            "open",
            "CONFIGURATION",
            "2026-01-07T00:00:00Z",
            "wiz",
        ),
        (
            DETECTION_ID_1,
            "Suspicious process",
            "high",
            None,
            "DETECTION",
            "2026-01-08T00:00:00Z",
            "wiz",
        ),
    }
    assert (
        {
            tuple(record.values())
            for record in neo4j_session.run(
                """
            MATCH (n:WizFinding:CVE)
            RETURN n.id, n._ont_cve_id, n._ont_base_severity, n._ont_source
            """,
            )
        }
        == {(VULNERABILITY_ID_1, CVE_ID_1, "high", "wiz")}
    )

    assert check_rels(
        neo4j_session,
        "WizTenant",
        "id",
        "WizIssue",
        "id",
        "RESOURCE",
    ) == {(TENANT_ID, ISSUE_ID_1)}
    assert check_rels(
        neo4j_session,
        "WizTenant",
        "id",
        "WizFinding",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, VULNERABILITY_ID_1),
        (TENANT_ID, NON_CVE_VULNERABILITY_ID),
        (TENANT_ID, CONFIGURATION_FINDING_ID_1),
        (TENANT_ID, DETECTION_ID_1),
    }
    assert check_rels(
        neo4j_session,
        "WizFinding",
        "id",
        "CVE",
        "id",
        "LINKED_TO",
    ) == {(VULNERABILITY_ID_1, CVE_ID_1)}


def test_start_wiz_ingestion_removes_stale_records_on_second_sync(
    neo4j_session,
    mocker,
):
    # Arrange
    _seed_cve(neo4j_session)
    mocker.patch("cartography.intel.wiz.get_access_token", return_value="token-1")
    mocker.patch("cartography.intel.wiz.issues.get", side_effect=[ISSUES, []])
    mocker.patch("cartography.intel.wiz.findings.get", side_effect=[FINDINGS, []])

    # Act
    cartography.intel.wiz.start_wiz_ingestion(neo4j_session, _config(TEST_UPDATE_TAG))
    cartography.intel.wiz.start_wiz_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(neo4j_session, "WizIssue", ["id"]) == set()
    assert check_nodes(neo4j_session, "WizFinding", ["id"]) == set()


def test_start_wiz_ingestion_lookback_mode_preserves_older_records(
    neo4j_session,
    mocker,
):
    # Arrange
    _seed_cve(neo4j_session)
    mocker.patch("cartography.intel.wiz.get_access_token", return_value="token-1")
    mocker.patch("cartography.intel.wiz.issues.get", side_effect=[ISSUES, []])
    mocker.patch("cartography.intel.wiz.findings.get", side_effect=[FINDINGS, []])

    # Act
    cartography.intel.wiz.start_wiz_ingestion(neo4j_session, _config(TEST_UPDATE_TAG))
    cartography.intel.wiz.start_wiz_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1, lookback_days=30),
    )

    # Assert
    assert check_nodes(neo4j_session, "WizIssue", ["id"]) == {
        (ISSUE_ID_1,),
    }
    assert check_nodes(neo4j_session, "WizFinding", ["id"]) == {
        (VULNERABILITY_ID_1,),
        (NON_CVE_VULNERABILITY_ID,),
        (CONFIGURATION_FINDING_ID_1,),
        (DETECTION_ID_1,),
    }


def test_start_wiz_ingestion_project_filter_preserves_older_records(
    neo4j_session,
    mocker,
):
    # Arrange
    _seed_cve(neo4j_session)
    mocker.patch("cartography.intel.wiz.get_access_token", return_value="token-1")
    mocker.patch("cartography.intel.wiz.issues.get", side_effect=[ISSUES, []])
    mocker.patch("cartography.intel.wiz.findings.get", side_effect=[FINDINGS, []])

    # Act
    cartography.intel.wiz.start_wiz_ingestion(neo4j_session, _config(TEST_UPDATE_TAG))
    cartography.intel.wiz.start_wiz_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1, project_ids=["project-1"]),
    )

    # Assert
    assert check_nodes(neo4j_session, "WizIssue", ["id"]) == {
        (ISSUE_ID_1,),
    }
    assert check_nodes(neo4j_session, "WizFinding", ["id"]) == {
        (VULNERABILITY_ID_1,),
        (NON_CVE_VULNERABILITY_ID,),
        (CONFIGURATION_FINDING_ID_1,),
        (DETECTION_ID_1,),
    }
