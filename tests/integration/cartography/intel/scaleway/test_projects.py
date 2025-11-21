from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.projects
import tests.data.scaleway.projects
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


def _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session):
    data = cartography.intel.scaleway.projects.transform_projects(
        tests.data.scaleway.projects.SCALEWAY_PROJECTS
    )
    cartography.intel.scaleway.projects.load_projects(
        neo4j_session, data, TEST_ORG_ID, TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.scaleway.projects,
    "get",
    return_value=tests.data.scaleway.projects.SCALEWAY_PROJECTS,
)
def test_load_scaleway_projects(mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }

    # Act
    cartography.intel.scaleway.projects.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Projects exist
    expected_nodes = {
        (
            "0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
            "default",
        )
    }
    assert (
        check_nodes(neo4j_session, "ScalewayProject", ["id", "name"]) == expected_nodes
    )

    # Assert Oganization exists
    assert check_nodes(neo4j_session, "ScalewayOrganization", ["id"]) == {
        (TEST_ORG_ID,)
    }

    # Assert projects are linked to the organization
    expected_rels = {
        (
            "0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
            "0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayProject",
            "id",
            "ScalewayOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
