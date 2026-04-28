from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.firewall as firewall
from tests.data.azure.firewall import DESCRIBE_FIREWALL_POLICIES
from tests.data.azure.firewall import DESCRIBE_FIREWALLS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.firewall.get_ip_groups")
@patch("cartography.intel.azure.firewall.get_firewall_policy_rule_groups")
@patch("cartography.intel.azure.firewall.get_firewall_policies")
@patch("cartography.intel.azure.firewall.get_firewalls")
@patch("cartography.intel.azure.firewall.get_client")
def test_sync_azure_firewalls(
    mock_get_client,
    mock_get_firewalls,
    mock_get_policies,
    mock_get_rule_groups,
    mock_get_ip_groups,
    neo4j_session,
):
    """
    Test that we can correctly sync Azure Firewall, Firewall Policy,
    and Firewall IP Configuration data and their relationships.
    """
    # Arrange
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_get_firewalls.return_value = DESCRIBE_FIREWALLS
    mock_get_policies.return_value = DESCRIBE_FIREWALL_POLICIES
    mock_get_rule_groups.return_value = []  # No rule groups for this test
    mock_get_ip_groups.return_value = []  # No IP groups for this test

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    # Create prerequisite AzureVirtualNetwork node for firewall-1
    neo4j_session.run(
        """
        MERGE (vnet:AzureVirtualNetwork{id: $vnet_id})
        SET vnet.lastupdated = $tag
        """,
        vnet_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet",
        tag=TEST_UPDATE_TAG,
    )

    # Create prerequisite AzureSubnet nodes for IP configurations
    neo4j_session.run(
        """
        MERGE (subnet:AzureSubnet{id: $subnet_id})
        SET subnet.lastupdated = $tag
        """,
        subnet_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/AzureFirewallSubnet",
        tag=TEST_UPDATE_TAG,
    )

    neo4j_session.run(
        """
        MERGE (subnet:AzureSubnet{id: $subnet_id})
        SET subnet.lastupdated = $tag
        """,
        subnet_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/AzureFirewallManagementSubnet",
        tag=TEST_UPDATE_TAG,
    )

    # Create prerequisite AzurePublicIPAddress nodes for IP configurations
    public_ip_ids = [
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-pip-1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-pip-2",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-mgmt-pip",
    ]
    for pip_id in public_ip_ids:
        neo4j_session.run(
            """
            MERGE (pip:AzurePublicIPAddress{id: $pip_id})
            SET pip.lastupdated = $tag
            """,
            pip_id=pip_id,
            tag=TEST_UPDATE_TAG,
        )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    firewall.sync(
        neo4j_session,
        mock_client,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check AzureFirewall nodes
    expected_firewall_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1",
            "test-firewall-1",
            "eastus",
            "Premium",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-2",
            "test-firewall-2",
            "westus",
            "Standard",
        ),
    }
    assert (
        check_nodes(
            neo4j_session, "AzureFirewall", ["id", "name", "location", "sku_tier"]
        )
        == expected_firewall_nodes
    )

    # Assert - Check AzureFirewallPolicy nodes
    expected_policy_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-1",
            "test-policy-1",
            "Alert",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-2",
            "test-policy-2",
            "Deny",
        ),
    }
    assert (
        check_nodes(
            neo4j_session, "AzureFirewallPolicy", ["id", "name", "threat_intel_mode"]
        )
        == expected_policy_nodes
    )

    # Assert - Check AzureSubscription -> AzureFirewallPolicy relationship
    # The relationship direction is INWARD, meaning (:AzureSubscription)-[:RESOURCE]->(:AzureFirewallPolicy)
    expected_sub_policy_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureFirewallPolicy",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_sub_policy_rels
    )

    # Assert - Check AzureFirewallPolicy -> AzureFirewallPolicy (INHERITS_FROM) relationship
    # test-policy-2 inherits from test-policy-1 (parent/base policy)
    expected_policy_inheritance_rels = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-1",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureFirewallPolicy",
            "id",
            "AzureFirewallPolicy",
            "id",
            "INHERITS_FROM",
            rel_direction_right=True,
        )
        == expected_policy_inheritance_rels
    )

    # Assert - Check AzureFirewallIPConfiguration nodes
    expected_ip_config_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig1",
            "ipconfig1",
            "10.0.1.4",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig2",
            "ipconfig2",
            "10.0.1.5",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/mgmt-ipconfig",
            "mgmt-ipconfig",
            "10.0.1.10",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "AzureFirewallIPConfiguration",
            ["id", "name", "private_ip_address"],
        )
        == expected_ip_config_nodes
    )

    # Assert - Check AzureSubscription <- AzureFirewall relationship
    # The relationship direction is INWARD, meaning (:AzureSubscription)<-[:RESOURCE]-(:AzureFirewall)
    expected_sub_fw_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureFirewall",
            "id",
            "RESOURCE",
            rel_direction_right=True,  # Changed from False - relationship points from Firewall to Subscription
        )
        == expected_sub_fw_rels
    )

    # Assert - Check AzureFirewall -> AzureFirewallPolicy relationship
    expected_fw_policy_rels = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureFirewall",
            "id",
            "AzureFirewallPolicy",
            "id",
            "USES_POLICY",
            rel_direction_right=True,
        )
        == expected_fw_policy_rels
    )

    # Assert - Check AzureFirewall <- AzureFirewallIPConfiguration relationship
    # The relationship direction is INWARD, meaning (:AzureFirewall)<-[:HAS_IP_CONFIGURATION]-(:AzureFirewallIPConfiguration)
    expected_fw_ipconfig_rels = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig2",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/mgmt-ipconfig",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureFirewall",
            "id",
            "AzureFirewallIPConfiguration",
            "id",
            "HAS_IP_CONFIGURATION",
            rel_direction_right=True,  # Changed from False - relationship points from IPConfig to Firewall
        )
        == expected_fw_ipconfig_rels
    )

    # Assert - Check AzureFirewallIPConfiguration -> AzureSubnet relationship
    expected_ipconfig_subnet_rels = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/AzureFirewallSubnet",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/AzureFirewallSubnet",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/mgmt-ipconfig",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/AzureFirewallManagementSubnet",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureFirewallIPConfiguration",
            "id",
            "AzureSubnet",
            "id",
            "IN_SUBNET",
            rel_direction_right=True,
        )
        == expected_ipconfig_subnet_rels
    )

    # Assert - Check AzureFirewallIPConfiguration -> AzurePublicIPAddress relationship
    expected_ipconfig_pip_rels = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-pip-1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-pip-2",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/mgmt-ipconfig",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-mgmt-pip",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureFirewallIPConfiguration",
            "id",
            "AzurePublicIPAddress",
            "id",
            "USES_PUBLIC_IP",
            rel_direction_right=True,
        )
        == expected_ipconfig_pip_rels
    )

    # Assert - Check AzureFirewall -> AzureVirtualNetwork relationship
    expected_fw_vnet_rels = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureFirewall",
            "id",
            "AzureVirtualNetwork",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_fw_vnet_rels
    )


@patch("cartography.intel.azure.firewall.get_ip_groups")
@patch("cartography.intel.azure.firewall.get_firewall_policy_rule_groups")
@patch("cartography.intel.azure.firewall.get_firewall_policies")
@patch("cartography.intel.azure.firewall.get_firewalls")
@patch("cartography.intel.azure.firewall.get_client")
def test_sync_azure_firewalls_cleanup(
    mock_get_client,
    mock_get_firewalls,
    mock_get_policies,
    mock_get_rule_groups,
    mock_get_ip_groups,
    neo4j_session,
):
    """
    Test that stale Azure Firewall data is properly cleaned up.
    """
    # Arrange - Create old data with different update tags
    old_update_tag = TEST_UPDATE_TAG - 1000

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    # Create old firewall that should be cleaned up
    neo4j_session.run(
        """
        MERGE (fw:AzureFirewall{id: $fw_id})
        SET fw.name = 'old-firewall', fw.lastupdated = $old_tag
        WITH fw
        MATCH (s:AzureSubscription{id: $sub_id})
        MERGE (fw)<-[r:RESOURCE]-(s)
        SET r.lastupdated = $old_tag
        """,
        fw_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/old-firewall",
        sub_id=TEST_SUBSCRIPTION_ID,
        old_tag=old_update_tag,
    )

    # Create old IP configuration that should be cleaned up
    neo4j_session.run(
        """
        MERGE (ip:AzureFirewallIPConfiguration{id: $ip_id})
        SET ip.name = 'old-ipconfig', ip.lastupdated = $old_tag
        WITH ip
        MATCH (s:AzureSubscription{id: $sub_id})
        MERGE (ip)<-[r:RESOURCE]-(s)
        SET r.lastupdated = $old_tag
        """,
        ip_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/old-firewall/azureFirewallIpConfigurations/old-ipconfig",
        sub_id=TEST_SUBSCRIPTION_ID,
        old_tag=old_update_tag,
    )

    # Create old policy that should be cleaned up
    neo4j_session.run(
        """
        MERGE (p:AzureFirewallPolicy{id: $policy_id})
        SET p.name = 'old-policy', p.lastupdated = $old_tag
        WITH p
        MATCH (s:AzureSubscription{id: $sub_id})
        MERGE (s)-[r:RESOURCE]->(p)
        SET r.lastupdated = $old_tag
        """,
        policy_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/old-policy",
        sub_id=TEST_SUBSCRIPTION_ID,
        old_tag=old_update_tag,
    )

    # Mock empty results from API (simulating resources were deleted)
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_get_firewalls.return_value = []
    mock_get_policies.return_value = []
    mock_get_rule_groups.return_value = []
    mock_get_ip_groups.return_value = []

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    firewall.sync(
        neo4j_session,
        mock_client,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Old firewall should be removed
    result = neo4j_session.run(
        "MATCH (fw:AzureFirewall{name: 'old-firewall'}) RETURN count(fw) as count"
    )
    assert result.single()["count"] == 0

    # Assert - Old IP configuration should be removed
    result = neo4j_session.run(
        "MATCH (ip:AzureFirewallIPConfiguration{name: 'old-ipconfig'}) RETURN count(ip) as count"
    )
    assert result.single()["count"] == 0

    # Assert - Old policy should be removed
    result = neo4j_session.run(
        "MATCH (p:AzureFirewallPolicy{name: 'old-policy'}) RETURN count(p) as count"
    )
    assert result.single()["count"] == 0
