from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.network.private_networks
import cartography.intel.scaleway.network.public_gateways
from tests.data.scaleway.network import SCALEWAY_PRIVATE_NETWORKS
from tests.data.scaleway.network import TEST_PRIVATE_NETWORK_ID
from tests.data.scaleway.public_gateways import SCALEWAY_PAT_RULES
from tests.data.scaleway.public_gateways import SCALEWAY_PUBLIC_GATEWAYS
from tests.data.scaleway.public_gateways import TEST_GATEWAY_ID
from tests.data.scaleway.public_gateways import TEST_PAT_RULE_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.network.private_networks,
    "get",
    return_value=SCALEWAY_PRIVATE_NETWORKS,
)
@patch.object(
    cartography.intel.scaleway.network.public_gateways,
    "get",
    return_value=(SCALEWAY_PUBLIC_GATEWAYS, SCALEWAY_PAT_RULES),
)
def test_load_scaleway_public_gateways(_mock_gw_get, _mock_pn_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    # Private networks must exist for the ATTACHED_TO edge to resolve.
    cartography.intel.scaleway.network.private_networks.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.scaleway.network.public_gateways.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(
        neo4j_session,
        "ScalewayPublicGateway",
        ["id", "name", "ipv4_address", "bastion_enabled"],
    ) == {(TEST_GATEWAY_ID, "demo-gateway", "51.15.1.1", True)}
    assert check_nodes(
        neo4j_session,
        "ScalewayPublicGatewayPatRule",
        ["id", "public_port", "private_port", "protocol"],
    ) == {(TEST_PAT_RULE_ID, 2222, 22, "tcp")}

    # Project ownership.
    for label in ("ScalewayPublicGateway", "ScalewayPublicGatewayPatRule"):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Gateway -> PatRule
    assert check_rels(
        neo4j_session,
        "ScalewayPublicGateway",
        "id",
        "ScalewayPublicGatewayPatRule",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_GATEWAY_ID, TEST_PAT_RULE_ID)}

    # Gateway -> PrivateNetwork (NAT / egress edge)
    assert check_rels(
        neo4j_session,
        "ScalewayPublicGateway",
        "id",
        "ScalewayPrivateNetwork",
        "id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {(TEST_GATEWAY_ID, TEST_PRIVATE_NETWORK_ID)}
