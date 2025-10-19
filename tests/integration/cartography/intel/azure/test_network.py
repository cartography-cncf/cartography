from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.network as network
from tests.data.azure.network import MOCK_NSGS
from tests.data.azure.network import MOCK_SUBNETS
from tests.data.azure.network import MOCK_VNETS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.network.get_network_security_groups")
@patch("cartography.intel.azure.network.get_subnets")
@patch("cartography.intel.azure.network.get_virtual_networks")
def test_sync_network(mock_get_vnets, mock_get_subnets, mock_get_nsgs, neo4j_session):
    """
    Test that we can correctly sync VNet, Subnet, and NSG data and their relationships.
    """
    # Arrange
    mock_get_vnets.return_value = MOCK_VNETS
    mock_get_subnets.return_value = MOCK_SUBNETS
    mock_get_nsgs.return_value = MOCK_NSGS

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    network.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes for all three types
    assert check_nodes(neo4j_session, "AzureVirtualNetwork", ["id"]) == {
        (MOCK_VNETS[0]["id"],)
    }
    assert check_nodes(neo4j_session, "AzureNetworkSecurityGroup", ["id"]) == {
        (MOCK_NSGS[0]["id"],)
    }
    expected_subnets = {(s["id"],) for s in MOCK_SUBNETS}
    assert check_nodes(neo4j_session, "AzureSubnet", ["id"]) == expected_subnets

    # Assert Relationships
    vnet_id = MOCK_VNETS[0]["id"]
    nsg_id = MOCK_NSGS[0]["id"]
    subnet_with_nsg_id = MOCK_SUBNETS[0]["id"]
    subnet_without_nsg_id = MOCK_SUBNETS[1]["id"]

    # Test parent relationships (:RESOURCE, :CONTAINS)
    expected_parent_rels = {
        (TEST_SUBSCRIPTION_ID, vnet_id),
        (TEST_SUBSCRIPTION_ID, nsg_id),
        (vnet_id, subnet_with_nsg_id),
        (vnet_id, subnet_without_nsg_id),
        (TEST_SUBSCRIPTION_ID, subnet_with_nsg_id),
        (TEST_SUBSCRIPTION_ID, subnet_without_nsg_id),
    }
    actual_parent_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureVirtualNetwork",
        "id",
        "RESOURCE",
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureNetworkSecurityGroup",
            "id",
            "RESOURCE",
        ),
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureVirtualNetwork",
            "id",
            "AzureSubnet",
            "id",
            "CONTAINS",
        ),
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureSubnet",
            "id",
            "RESOURCE",
        ),
    )
    assert actual_parent_rels == expected_parent_rels

    # Test association relationship (:ASSOCIATED_WITH)
    # Only one subnet should have this relationship
    expected_assoc_rels = {(subnet_with_nsg_id, nsg_id)}
    actual_assoc_rels = check_rels(
        neo4j_session,
        "AzureSubnet",
        "id",
        "AzureNetworkSecurityGroup",
        "id",
        "ASSOCIATED_WITH",
    )
    assert actual_assoc_rels == expected_assoc_rels
