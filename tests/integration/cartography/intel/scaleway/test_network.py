from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.network.ips
import cartography.intel.scaleway.network.private_networks
import cartography.intel.scaleway.network.vpcs
from tests.data.scaleway.network import SCALEWAY_IPS
from tests.data.scaleway.network import SCALEWAY_PRIVATE_NETWORKS
from tests.data.scaleway.network import SCALEWAY_VPCS
from tests.data.scaleway.network import TEST_IP_ID
from tests.data.scaleway.network import TEST_PRIVATE_NETWORK_ID
from tests.data.scaleway.network import TEST_SUBNET_ID
from tests.data.scaleway.network import TEST_VPC_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.network.vpcs, "get", return_value=SCALEWAY_VPCS
)
@patch.object(
    cartography.intel.scaleway.network.private_networks,
    "get",
    return_value=SCALEWAY_PRIVATE_NETWORKS,
)
@patch.object(cartography.intel.scaleway.network.ips, "get", return_value=SCALEWAY_IPS)
def test_load_scaleway_network(_mock_ips, _mock_pn, _mock_vpc, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    for module in (
        cartography.intel.scaleway.network.vpcs,
        cartography.intel.scaleway.network.private_networks,
        cartography.intel.scaleway.network.ips,
    ):
        module.sync(
            neo4j_session,
            client,
            common_job_parameters,
            org_id=TEST_ORG_ID,
            projects_id=[TEST_PROJECT_ID],
            update_tag=TEST_UPDATE_TAG,
        )

    # Assert nodes exist
    assert check_nodes(neo4j_session, "ScalewayVpc", ["id", "name"]) == {
        (TEST_VPC_ID, "demo-vpc"),
    }
    assert check_nodes(neo4j_session, "ScalewayPrivateNetwork", ["id", "name"]) == {
        (TEST_PRIVATE_NETWORK_ID, "demo-pn"),
    }
    assert check_nodes(neo4j_session, "ScalewaySubnet", ["id", "subnet"]) == {
        (TEST_SUBNET_ID, "172.16.8.0/22"),
    }
    assert check_nodes(neo4j_session, "ScalewayIP", ["id", "address"]) == {
        (TEST_IP_ID, "172.16.8.2/22"),
    }

    # Assert cross-cloud ontology labels are applied
    assert check_nodes(neo4j_session, "VirtualNetwork", ["id"]) == {(TEST_VPC_ID,)}
    assert check_nodes(neo4j_session, "Subnet", ["id"]) == {(TEST_SUBNET_ID,)}

    # Assert everything is linked to the project
    for label in (
        "ScalewayVpc",
        "ScalewayPrivateNetwork",
        "ScalewaySubnet",
        "ScalewayIP",
    ):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Assert VPC -> PrivateNetwork
    assert check_rels(
        neo4j_session,
        "ScalewayVpc",
        "id",
        "ScalewayPrivateNetwork",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_VPC_ID, TEST_PRIVATE_NETWORK_ID)}

    # Assert PrivateNetwork -> Subnet
    assert check_rels(
        neo4j_session,
        "ScalewayPrivateNetwork",
        "id",
        "ScalewaySubnet",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_PRIVATE_NETWORK_ID, TEST_SUBNET_ID)}

    # Assert Subnet -> IP
    assert check_rels(
        neo4j_session,
        "ScalewaySubnet",
        "id",
        "ScalewayIP",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_SUBNET_ID, TEST_IP_ID)}
