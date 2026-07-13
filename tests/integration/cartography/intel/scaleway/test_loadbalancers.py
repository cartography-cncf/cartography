from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.loadbalancers.loadbalancers
from tests.data.scaleway.loadbalancers import SCALEWAY_LB_BACKENDS
from tests.data.scaleway.loadbalancers import SCALEWAY_LB_FRONTENDS
from tests.data.scaleway.loadbalancers import SCALEWAY_LOADBALANCERS
from tests.data.scaleway.loadbalancers import TEST_BACKEND_ID
from tests.data.scaleway.loadbalancers import TEST_FRONTEND_ID
from tests.data.scaleway.loadbalancers import TEST_LB_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.loadbalancers.loadbalancers,
    "get",
    return_value=(
        SCALEWAY_LOADBALANCERS,
        SCALEWAY_LB_FRONTENDS,
        SCALEWAY_LB_BACKENDS,
    ),
)
def test_load_scaleway_loadbalancers(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.loadbalancers.loadbalancers.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes exist
    assert check_nodes(neo4j_session, "ScalewayLoadBalancer", ["id", "name"]) == {
        (TEST_LB_ID, "demo-lb"),
    }
    assert check_nodes(neo4j_session, "ScalewayLBFrontend", ["id", "name"]) == {
        (TEST_FRONTEND_ID, "demo-frontend"),
    }
    assert check_nodes(neo4j_session, "ScalewayLBBackend", ["id", "name"]) == {
        (TEST_BACKEND_ID, "demo-backend"),
    }

    # Assert the public IP is flattened onto the LB node
    assert check_nodes(neo4j_session, "ScalewayLoadBalancer", ["id", "ip_address"]) == {
        (TEST_LB_ID, "51.159.0.1"),
    }

    # Assert cross-cloud ontology label is applied
    assert check_nodes(neo4j_session, "LoadBalancer", ["id"]) == {(TEST_LB_ID,)}

    # Assert everything is linked to the project
    for label in ("ScalewayLoadBalancer", "ScalewayLBFrontend", "ScalewayLBBackend"):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Assert LB -> Frontend / Backend
    assert check_rels(
        neo4j_session,
        "ScalewayLoadBalancer",
        "id",
        "ScalewayLBFrontend",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_LB_ID, TEST_FRONTEND_ID)}
    assert check_rels(
        neo4j_session,
        "ScalewayLoadBalancer",
        "id",
        "ScalewayLBBackend",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_LB_ID, TEST_BACKEND_ID)}

    # Assert Frontend -> Backend
    assert check_rels(
        neo4j_session,
        "ScalewayLBFrontend",
        "id",
        "ScalewayLBBackend",
        "id",
        "ROUTES_TO",
        rel_direction_right=True,
    ) == {(TEST_FRONTEND_ID, TEST_BACKEND_ID)}
