import pytest

import cartography.intel.wiz
from cartography.config import Config
from tests.data.wiz import AUTH_URL
from tests.data.wiz import CLIENT_ID
from tests.data.wiz import CLIENT_SECRET
from tests.data.wiz import CVE_ID_1
from tests.data.wiz import GRAPHQL_URL
from tests.data.wiz import ISSUE_ID_1
from tests.data.wiz import ISSUES
from tests.data.wiz import RESOURCE_ID_1
from tests.data.wiz import RESOURCE_ID_2
from tests.data.wiz import RESOURCES
from tests.data.wiz import TENANT_ID
from tests.data.wiz import VULNERABILITY_FINDINGS
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
           OR n:WizResource
           OR n:WizIssue
           OR n:WizVulnerabilityFinding
        DETACH DELETE n
        """,
    )
    neo4j_session.run("MATCH (n:CVE {id: $id}) DETACH DELETE n", id=CVE_ID_1)
    yield
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:WizTenant
           OR n:WizResource
           OR n:WizIssue
           OR n:WizVulnerabilityFinding
        DETACH DELETE n
        """,
    )
    neo4j_session.run("MATCH (n:CVE {id: $id}) DETACH DELETE n", id=CVE_ID_1)


def _config(update_tag: int = TEST_UPDATE_TAG) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        wiz_graphql_url=GRAPHQL_URL,
        wiz_auth_url=AUTH_URL,
        wiz_client_id=CLIENT_ID,
        wiz_client_secret=CLIENT_SECRET,
        wiz_tenant_id=TENANT_ID,
        wiz_lookback_days=180,
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


def _patch_wiz_api(
    mocker, resources=RESOURCES, issues=ISSUES, vulnerabilities=VULNERABILITY_FINDINGS
):
    mocker.patch("cartography.intel.wiz.get_access_token", return_value="token-1")
    mocker.patch("cartography.intel.wiz.resources.get", return_value=resources)
    mocker.patch("cartography.intel.wiz.issues.get", return_value=issues)
    mocker.patch(
        "cartography.intel.wiz.vulnerabilities.get",
        return_value=vulnerabilities,
    )


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
        "WizResource",
        ["id", "name", "cloud_platform"],
    ) == {
        (RESOURCE_ID_1, "prod-instance", "AWS"),
        (RESOURCE_ID_2, "stale-instance", "AWS"),
    }
    assert check_nodes(
        neo4j_session,
        "WizIssue",
        ["id", "severity", "status", "resource_id"],
    ) == {
        (ISSUE_ID_1, "HIGH", "OPEN", RESOURCE_ID_1),
    }
    assert check_nodes(
        neo4j_session,
        "WizVulnerabilityFinding",
        ["id", "cve_id", "resource_id"],
    ) == {
        (VULNERABILITY_ID_1, CVE_ID_1, RESOURCE_ID_1),
    }

    assert check_rels(
        neo4j_session,
        "WizTenant",
        "id",
        "WizResource",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, RESOURCE_ID_1),
        (TENANT_ID, RESOURCE_ID_2),
    }
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
        "WizVulnerabilityFinding",
        "id",
        "RESOURCE",
    ) == {(TENANT_ID, VULNERABILITY_ID_1)}
    assert check_rels(
        neo4j_session,
        "WizIssue",
        "id",
        "WizResource",
        "id",
        "AFFECTS",
    ) == {(ISSUE_ID_1, RESOURCE_ID_1)}
    assert check_rels(
        neo4j_session,
        "WizVulnerabilityFinding",
        "id",
        "WizResource",
        "id",
        "AFFECTS",
    ) == {(VULNERABILITY_ID_1, RESOURCE_ID_1)}
    assert check_rels(
        neo4j_session,
        "WizVulnerabilityFinding",
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
    mocker.patch(
        "cartography.intel.wiz.resources.get",
        side_effect=[RESOURCES, RESOURCES[:1]],
    )
    mocker.patch("cartography.intel.wiz.issues.get", side_effect=[ISSUES, []])
    mocker.patch(
        "cartography.intel.wiz.vulnerabilities.get",
        side_effect=[VULNERABILITY_FINDINGS, []],
    )

    # Act
    cartography.intel.wiz.start_wiz_ingestion(neo4j_session, _config(TEST_UPDATE_TAG))
    cartography.intel.wiz.start_wiz_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(neo4j_session, "WizResource", ["id"]) == {
        (RESOURCE_ID_1,),
    }
    assert check_nodes(neo4j_session, "WizIssue", ["id"]) == set()
    assert check_nodes(neo4j_session, "WizVulnerabilityFinding", ["id"]) == set()
    assert check_rels(
        neo4j_session,
        "WizTenant",
        "id",
        "WizResource",
        "id",
        "RESOURCE",
    ) == {(TENANT_ID, RESOURCE_ID_1)}
