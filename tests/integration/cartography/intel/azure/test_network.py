from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.network as network
from tests.data.azure.network import MOCK_NETWORK_INTERFACES
from tests.data.azure.network import MOCK_NSGS
from tests.data.azure.network import MOCK_PUBLIC_IPS
from tests.data.azure.network import MOCK_SUBNETS
from tests.data.azure.network import MOCK_VNETS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.network.get_network_interfaces")
@patch("cartography.intel.azure.network.get_public_ip_addresses")
@patch("cartography.intel.azure.network.get_network_security_groups")
@patch("cartography.intel.azure.network.get_subnets")
@patch("cartography.intel.azure.network.get_virtual_networks")
def test_sync_network(
    mock_get_vnets,
    mock_get_subnets,
    mock_get_nsgs,
    mock_get_public_ips,
    mock_get_nics,
    neo4j_session,
):
    """
    Test that we can correctly sync VNet, Subnet, NSG, Public IP, and Network Interface
    data and their relationships.
    """
    # Arrange
    mock_get_vnets.return_value = MOCK_VNETS
    mock_get_subnets.return_value = MOCK_SUBNETS
    mock_get_nsgs.return_value = MOCK_NSGS
    mock_get_public_ips.return_value = MOCK_PUBLIC_IPS
    mock_get_nics.return_value = MOCK_NETWORK_INTERFACES

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    # Create prerequisite AzureVirtualMachine nodes for the NIC-VM relationships
    for nic in MOCK_NETWORK_INTERFACES:
        if nic.get("virtual_machine"):
            vm_id = nic["virtual_machine"]["id"]
            neo4j_session.run(
                "MERGE (vm:AzureVirtualMachine{id: $vm_id}) SET vm.lastupdated = $tag",
                vm_id=vm_id,
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

    # Assert Public IP Address nodes
    expected_public_ips = set()
    for pip in MOCK_PUBLIC_IPS:
        pip_properties = pip.get("properties", {})
        expected_public_ips.add(
            (
                pip["id"],
                pip_properties.get("ip_address") or pip.get("ip_address"),
                pip_properties.get("public_ip_allocation_method")
                or pip.get("public_ip_allocation_method"),
            ),
        )
    assert (
        check_nodes(
            neo4j_session,
            "AzurePublicIPAddress",
            ["id", "ip_address", "allocation_method"],
        )
        == expected_public_ips
    )

    # Assert Network Interface nodes
    expected_nics = {(nic["id"],) for nic in MOCK_NETWORK_INTERFACES}
    assert check_nodes(neo4j_session, "AzureNetworkInterface", ["id"]) == expected_nics

    # Test Public IP to Subscription relationship
    expected_pip_sub_rels = {
        (TEST_SUBSCRIPTION_ID, pip["id"]) for pip in MOCK_PUBLIC_IPS
    }
    actual_pip_sub_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzurePublicIPAddress",
        "id",
        "RESOURCE",
    )
    assert actual_pip_sub_rels == expected_pip_sub_rels

    # Test Network Interface to Subscription relationship
    expected_nic_sub_rels = {
        (TEST_SUBSCRIPTION_ID, nic["id"]) for nic in MOCK_NETWORK_INTERFACES
    }
    actual_nic_sub_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureNetworkInterface",
        "id",
        "RESOURCE",
    )
    assert actual_nic_sub_rels == expected_nic_sub_rels

    # Test Network Interface to Virtual Machine relationship
    # Only NICs with virtual_machine should have this relationship
    # Relationship direction: (NIC)-[:ATTACHED_TO]->(VM) - "NIC is attached to VM"
    expected_nic_vm_rels = set()
    for nic in MOCK_NETWORK_INTERFACES:
        if nic.get("virtual_machine"):
            expected_nic_vm_rels.add((nic["id"], nic["virtual_machine"]["id"]))

    actual_nic_vm_rels = check_rels(
        neo4j_session,
        "AzureNetworkInterface",
        "id",
        "AzureVirtualMachine",
        "id",
        "ATTACHED_TO",
    )
    assert actual_nic_vm_rels == expected_nic_vm_rels

    # Test Network Interface to Subnet relationship
    # Test data uses flattened structure (matching real Azure SDK as_dict() output)
    expected_nic_subnet_rels = set()
    for nic in MOCK_NETWORK_INTERFACES:
        for ip_config in nic.get("ip_configurations", []):
            subnet = ip_config.get("subnet", {})
            if subnet and subnet.get("id"):
                expected_nic_subnet_rels.add((nic["id"], subnet["id"]))

    actual_nic_subnet_rels = check_rels(
        neo4j_session,
        "AzureNetworkInterface",
        "id",
        "AzureSubnet",
        "id",
        "ATTACHED_TO",
    )
    assert actual_nic_subnet_rels == expected_nic_subnet_rels

    # Test Network Interface to Public IP relationship
    # Test data uses flattened structure (matching real Azure SDK as_dict() output)
    expected_nic_pip_rels = set()
    for nic in MOCK_NETWORK_INTERFACES:
        for ip_config in nic.get("ip_configurations", []):
            pip = ip_config.get("public_ip_address", {})
            if pip and pip.get("id"):
                expected_nic_pip_rels.add((nic["id"], pip["id"]))

    actual_nic_pip_rels = check_rels(
        neo4j_session,
        "AzureNetworkInterface",
        "id",
        "AzurePublicIPAddress",
        "id",
        "ASSOCIATED_WITH",
    )
    assert actual_nic_pip_rels == expected_nic_pip_rels
