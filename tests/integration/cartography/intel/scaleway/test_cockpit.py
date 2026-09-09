from unittest.mock import Mock
from unittest.mock import patch

import pytest

import cartography.intel.scaleway.cockpit.cockpit
from tests.data.scaleway.cockpit import SCALEWAY_COCKPIT_DATA_SOURCES
from tests.data.scaleway.cockpit import SCALEWAY_COCKPIT_PLAN
from tests.data.scaleway.cockpit import SCALEWAY_COCKPIT_TOKENS
from tests.data.scaleway.cockpit import TEST_DATA_SOURCE_ID
from tests.data.scaleway.cockpit import TEST_TOKEN_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_SKIPPED_PROJECT_ID = "11111111-1111-1111-1111-111111111111"
TEST_SKIPPED_DATA_SOURCE_ID = "22222222-2222-2222-2222-222222222222"


@pytest.fixture(autouse=True)
def _reset_graph_between_tests(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    yield
    neo4j_session.run("MATCH (n) DETACH DELETE n")


@patch.object(
    cartography.intel.scaleway.cockpit.cockpit,
    "get",
    return_value=(
        {TEST_PROJECT_ID: SCALEWAY_COCKPIT_PLAN},
        SCALEWAY_COCKPIT_DATA_SOURCES,
        SCALEWAY_COCKPIT_TOKENS,
        [TEST_PROJECT_ID],
    ),
)
def test_load_scaleway_cockpit(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.cockpit.cockpit.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "ScalewayCockpit", ["id", "plan_name"]) == {
        (TEST_PROJECT_ID, "free"),
    }
    assert check_nodes(neo4j_session, "ScalewayCockpitDataSource", ["id", "name"]) == {
        (TEST_DATA_SOURCE_ID, "demo-metrics"),
    }
    assert check_nodes(neo4j_session, "ScalewayCockpitToken", ["id", "name"]) == {
        (TEST_TOKEN_ID, "demo-token"),
    }

    # The token's plaintext secret_key must never reach the graph.
    token_props = neo4j_session.run(
        "MATCH (n:ScalewayCockpitToken {id: $id}) RETURN properties(n) AS props",
        id=TEST_TOKEN_ID,
    ).single()["props"]
    assert "secret_key" not in token_props

    # Cross-cloud ontology label
    assert check_nodes(neo4j_session, "Secret", ["id"]) == {(TEST_TOKEN_ID,)}

    # Project ownership
    assert check_rels(
        neo4j_session,
        "ScalewayCockpit",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(TEST_PROJECT_ID, TEST_PROJECT_ID)}
    assert check_rels(
        neo4j_session,
        "ScalewayCockpitDataSource",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(TEST_DATA_SOURCE_ID, TEST_PROJECT_ID)}
    assert check_rels(
        neo4j_session,
        "ScalewayCockpitToken",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(TEST_TOKEN_ID, TEST_PROJECT_ID)}

    # Cockpit -> DataSource / Token
    assert check_rels(
        neo4j_session,
        "ScalewayCockpit",
        "id",
        "ScalewayCockpitDataSource",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_PROJECT_ID, TEST_DATA_SOURCE_ID)}
    assert check_rels(
        neo4j_session,
        "ScalewayCockpit",
        "id",
        "ScalewayCockpitToken",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_PROJECT_ID, TEST_TOKEN_ID)}


@patch.object(
    cartography.intel.scaleway.cockpit.cockpit,
    "get",
    return_value=(
        {TEST_PROJECT_ID: SCALEWAY_COCKPIT_PLAN},
        SCALEWAY_COCKPIT_DATA_SOURCES,
        SCALEWAY_COCKPIT_TOKENS,
        [TEST_PROJECT_ID],
    ),
)
def test_scaleway_cockpit_cleanup_removes_stale_resources(mock_get, neo4j_session):
    # Arrange: one full sync, then everything upstream is gone.
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    cartography.intel.scaleway.cockpit.cockpit.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Act: re-sync with an empty plan and no data sources/tokens upstream.
    mock_get.return_value = (
        {TEST_PROJECT_ID: SCALEWAY_COCKPIT_PLAN},
        [],
        [],
        [TEST_PROJECT_ID],
    )
    common_job_parameters["UPDATE_TAG"] = TEST_UPDATE_TAG + 1
    cartography.intel.scaleway.cockpit.cockpit.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Assert: stale data sources/tokens are gone, but the Cockpit itself survives
    # (still returned by get() every run - it's a project singleton, not a list).
    assert check_nodes(neo4j_session, "ScalewayCockpit", ["id"]) == {
        (TEST_PROJECT_ID,),
    }
    assert check_nodes(neo4j_session, "ScalewayCockpitDataSource", ["id"]) == set()
    assert check_nodes(neo4j_session, "ScalewayCockpitToken", ["id"]) == set()


@patch.object(
    cartography.intel.scaleway.cockpit.cockpit,
    "get",
    return_value=(
        {TEST_PROJECT_ID: SCALEWAY_COCKPIT_PLAN},
        SCALEWAY_COCKPIT_DATA_SOURCES,
        SCALEWAY_COCKPIT_TOKENS,
        [TEST_PROJECT_ID],
    ),
)
def test_scaleway_cockpit_cleanup_preserves_skipped_projects(_mock_get, neo4j_session):
    # Arrange: seed a stale data source under a second project that get() did not
    # fully enumerate. Cleanup must not treat the skipped project as an empty result.
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    neo4j_session.run(
        """
        MERGE (p:ScalewayProject {id: $project_id})
        SET p.firstseen = $old_update_tag,
            p.lastupdated = $old_update_tag,
            p.name = "skipped-project"
        MERGE (c:ScalewayCockpitDataSource {id: $data_source_id})
        SET c.firstseen = $old_update_tag,
            c.lastupdated = $old_update_tag,
            c.project_id = $project_id,
            c.name = "stale-skipped-project-source"
        MERGE (p)-[:RESOURCE {lastupdated: $old_update_tag}]->(c)
        """,
        project_id=TEST_SKIPPED_PROJECT_ID,
        data_source_id=TEST_SKIPPED_DATA_SOURCE_ID,
        old_update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.scaleway.cockpit.cockpit.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID, TEST_SKIPPED_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Assert: the successfully enumerated project is refreshed, while stale Cockpit
    # data under the skipped project is preserved for a future successful sync.
    assert check_nodes(
        neo4j_session,
        "ScalewayCockpitDataSource",
        ["id", "name"],
    ) == {
        (TEST_DATA_SOURCE_ID, "demo-metrics"),
        (TEST_SKIPPED_DATA_SOURCE_ID, "stale-skipped-project-source"),
    }
    assert check_rels(
        neo4j_session,
        "ScalewayCockpitDataSource",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_DATA_SOURCE_ID, TEST_PROJECT_ID),
        (TEST_SKIPPED_DATA_SOURCE_ID, TEST_SKIPPED_PROJECT_ID),
    }
