from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.instances.instances
import tests.data.scaleway.instances
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.cartography.intel.scaleway.test_storage import (
    _ensure_local_neo4j_has_test_volumes,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.instances.instances,
    "get",
    return_value=tests.data.scaleway.instances.SCALEWAY_INSTANCES,
)
def test_load_scaleway_instances(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_volumes(neo4j_session)

    # Act
    cartography.intel.scaleway.instances.instances.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Instances exist
    expected_nodes = {
        (
            "345627e9-18ff-47e0-b73d-3f38fddb4390",
            "demo-server",
        )
    }
    assert (
        check_nodes(neo4j_session, "ScalewayInstance", ["id", "name"]) == expected_nodes
    )

    # Assert Project exists
    assert check_nodes(neo4j_session, "ScalewayProject", ["id"]) == {(TEST_PROJECT_ID,)}

    # Assert instances are linked to the project
    expected_rels = {
        (
            "345627e9-18ff-47e0-b73d-3f38fddb4390",
            TEST_PROJECT_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayInstance",
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert instances are linked to volumes
    expected_volume_rels = {
        (
            "345627e9-18ff-47e0-b73d-3f38fddb4390",
            "7c37b328-247c-4668-8ee1-701a3a3cc2e4",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayInstance",
            "id",
            "ScalewayVolume",
            "id",
            "MOUNTS",
            rel_direction_right=True,
        )
        == expected_volume_rels
    )
