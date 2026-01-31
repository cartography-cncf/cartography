from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.compute
import tests.data.gcp.compute
from cartography.graph.job import GraphJob
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "project-abc"


def _create_test_project(neo4j_session, project_id: str, update_tag: int):
    """Helper to create a GCPProject node for testing."""
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        gcp_update_tag=update_tag,
    )


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_vpcs(mock_get_vpcs, neo4j_session):
    """Test sync_gcp_vpcs() loads VPCs and creates relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - VPC nodes created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPVpc",
        ["id", "name", "project_id", "auto_create_subnetworks"],
    ) == {
        (
            "projects/project-abc/global/networks/default",
            "default",
            "project-abc",
            True,
        ),
    }

    # Assert - Project to VPC relationship created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpc",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("project-abc", "projects/project-abc/global/networks/default"),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_subnets",
    return_value=tests.data.gcp.compute.VPC_SUBNET_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_subnets(mock_get_vpcs, mock_get_subnets, neo4j_session):
    """Test sync_gcp_subnets() loads subnets and creates relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs so subnets can connect to them
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_subnets(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Subnet nodes created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPSubnet",
        [
            "id",
            "region",
            "gateway_address",
            "ip_cidr_range",
            "private_ip_google_access",
        ],
    ) == {
        (
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "europe-west2",
            "10.0.0.1",
            "10.0.0.0/20",
            False,
        ),
    }

    # Assert - VPC to Subnet relationship created
    assert check_rels(
        neo4j_session,
        "GCPVpc",
        "id",
        "GCPSubnet",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/regions/europe-west2/subnetworks/default",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
def test_sync_gcp_instances(mock_get_instances, neo4j_session):
    """Test sync_gcp_instances() loads instances and creates relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    # Create project first - required for RESOURCE relationship with data model
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Instance nodes created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPInstance",
        ["id", "instancename", "zone_name", "project_id"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "instance-1",
            "europe-west2-b",
            "project-abc",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "instance-1-test",
            "europe-west2-b",
            "project-abc",
        ),
    }

    # Assert - Project to Instance relationship created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPInstance",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "project-abc",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
        ),
        (
            "project-abc",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
        ),
    }

    # Assert - Network interface nodes created
    assert check_nodes(
        neo4j_session,
        "GCPNetworkInterface",
        ["id", "name", "private_ip"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
            "nic0",
            "10.0.0.2",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
            "nic0",
            "10.0.0.3",
        ),
    }

    # Assert - Instance to NetworkInterface relationship created
    assert check_rels(
        neo4j_session,
        "GCPInstance",
        "id",
        "GCPNetworkInterface",
        "id",
        "NETWORK_INTERFACE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
        ),
    }

    # Assert - NetworkInterface to Subnet relationship created
    assert check_rels(
        neo4j_session,
        "GCPNetworkInterface",
        "id",
        "GCPSubnet",
        "id",
        "PART_OF_SUBNET",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
            "projects/project-abc/regions/europe-west2/subnetworks/default",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
            "projects/project-abc/regions/europe-west2/subnetworks/default",
        ),
    }

    # Assert - Access config nodes created
    assert check_nodes(
        neo4j_session,
        "GCPNicAccessConfig",
        ["id", "public_ip"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0/accessconfigs/ONE_TO_ONE_NAT",
            "1.2.3.4",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0/accessconfigs/ONE_TO_ONE_NAT",
            "1.3.4.5",
        ),
    }

    # Assert - NetworkInterface to AccessConfig relationship created
    assert check_rels(
        neo4j_session,
        "GCPNetworkInterface",
        "id",
        "GCPNicAccessConfig",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0/accessconfigs/ONE_TO_ONE_NAT",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0/accessconfigs/ONE_TO_ONE_NAT",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_subnets",
    return_value=tests.data.gcp.compute.VPC_SUBNET_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_instances_with_vpc_relationship(
    mock_get_vpcs, mock_get_subnets, mock_get_instances, neo4j_session
):
    """Test that instances are connected to VPCs via MEMBER_OF_GCP_VPC relationship."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Load VPCs and subnets first
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.compute.sync_gcp_subnets(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Run the analysis job to create MEMBER_OF_GCP_VPC relationships
    GraphJob.run_from_json_file(
        "cartography/data/jobs/analysis/gcp_compute_instance_vpc_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Instance to VPC relationship created
    assert check_rels(
        neo4j_session,
        "GCPInstance",
        "id",
        "GCPVpc",
        "id",
        "MEMBER_OF_GCP_VPC",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "projects/project-abc/global/networks/default",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "projects/project-abc/global/networks/default",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_instances_with_tags(mock_get_vpcs, mock_get_instances, neo4j_session):
    """Test that instances with tags create GCPNetworkTag nodes and relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs so tags can connect to them
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Network tag nodes created (only instance-1 has tags)
    assert check_nodes(
        neo4j_session,
        "GCPNetworkTag",
        ["id", "value"],
    ) == {
        (
            "projects/project-abc/global/networks/default/tags/test",
            "test",
        ),
    }

    # Assert - Instance to Tag relationship created
    assert check_rels(
        neo4j_session,
        "GCPInstance",
        "id",
        "GCPNetworkTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "projects/project-abc/global/networks/default/tags/test",
        ),
    }

    # Assert - Tag to VPC relationship created (Tag)-[DEFINED_IN]->(VPC)
    assert check_rels(
        neo4j_session,
        "GCPNetworkTag",
        "id",
        "GCPVpc",
        "id",
        "DEFINED_IN",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/default/tags/test",
            "projects/project-abc/global/networks/default",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_global_forwarding_rules",
    return_value=tests.data.gcp.compute.LIST_GLOBAL_FORWARDING_RULES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_regional_forwarding_rules",
    return_value=tests.data.gcp.compute.LIST_FORWARDING_RULES_RESPONSE,
)
def test_sync_gcp_forwarding_rules(mock_get_regional, mock_get_global, neo4j_session):
    """Test sync_gcp_forwarding_rules() loads both global and regional forwarding rules."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    # Act
    cartography.intel.gcp.compute.sync_gcp_forwarding_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Both global and regional forwarding rule nodes created
    assert check_nodes(
        neo4j_session,
        "GCPForwardingRule",
        ["id", "ip_address", "project_id", "region"],
    ) == {
        # Global rule (no region)
        (
            "projects/project-abc/global/forwardingRules/global-rule-1",
            "35.235.1.2",
            "project-abc",
            None,
        ),
        # Regional rules
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-service-1111",
            "10.0.0.10",
            "project-abc",
            "europe-west2",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/public-ingress-controller-1234567",
            "1.2.3.11",
            "project-abc",
            "europe-west2",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/shard-server-22222",
            "10.0.0.20",
            "project-abc",
            "europe-west2",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_global_forwarding_rules",
    return_value=tests.data.gcp.compute.LIST_GLOBAL_FORWARDING_RULES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_regional_forwarding_rules",
    return_value=tests.data.gcp.compute.LIST_FORWARDING_RULES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_subnets",
    return_value=tests.data.gcp.compute.VPC_SUBNET_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_forwarding_rules_with_relationships(
    mock_get_vpcs, mock_get_subnets, mock_get_regional, mock_get_global, neo4j_session
):
    """Test forwarding rules relationships: Subnet->ForwardingRule for regional, VPC->ForwardingRule for global."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs and subnets
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.compute.sync_gcp_subnets(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_forwarding_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Subnet to ForwardingRule relationship (for INTERNAL regional rules with subnetwork)
    assert check_rels(
        neo4j_session,
        "GCPSubnet",
        "id",
        "GCPForwardingRule",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-service-1111",
        ),
        (
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "projects/project-abc/regions/europe-west2/forwardingRules/shard-server-22222",
        ),
    }

    # Assert - VPC to ForwardingRule relationship (for global rules without subnetwork)
    assert check_rels(
        neo4j_session,
        "GCPVpc",
        "id",
        "GCPForwardingRule",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/forwardingRules/global-rule-1",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_firewall_ingress_rules",
    return_value=tests.data.gcp.compute.LIST_FIREWALLS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_firewall_rules(mock_get_vpcs, mock_get_firewalls, neo4j_session):
    """Test sync_gcp_firewall_rules() loads firewalls and creates relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs so firewalls can connect to them
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_firewall_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Firewall nodes created
    assert check_nodes(
        neo4j_session,
        "GCPFirewall",
        ["id", "name", "direction", "priority", "has_target_service_accounts"],
    ) == {
        (
            "projects/project-abc/global/firewalls/default-allow-icmp",
            "default-allow-icmp",
            "INGRESS",
            65534,
            False,
        ),
        (
            "projects/project-abc/global/firewalls/default-allow-internal",
            "default-allow-internal",
            "INGRESS",
            65534,
            False,
        ),
        (
            "projects/project-abc/global/firewalls/default-allow-rdp",
            "default-allow-rdp",
            "INGRESS",
            65534,
            False,
        ),
        (
            "projects/project-abc/global/firewalls/default-allow-ssh",
            "default-allow-ssh",
            "INGRESS",
            65534,
            False,
        ),
        (
            "projects/project-abc/global/firewalls/custom-port-incoming",
            "custom-port-incoming",
            "INGRESS",
            1000,
            False,
        ),
    }

    # Assert - VPC to Firewall relationship created
    assert check_rels(
        neo4j_session,
        "GCPVpc",
        "id",
        "GCPFirewall",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-icmp",
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-internal",
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-rdp",
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-ssh",
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/custom-port-incoming",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_firewall_ingress_rules",
    return_value=tests.data.gcp.compute.LIST_FIREWALLS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_firewall_rules_with_ip_rules(
    mock_get_vpcs, mock_get_firewalls, neo4j_session
):
    """Test that firewalls create IpRule and IpRange nodes with proper relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_firewall_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - IpRule nodes created (checking SSH rule as example)
    ip_rules = check_nodes(
        neo4j_session,
        "IpRule",
        ["id", "protocol", "fromport", "toport"],
    )
    # The SSH rule should exist
    assert (
        "projects/project-abc/global/firewalls/default-allow-ssh/allow/22tcp",
        "tcp",
        22,
        22,
    ) in ip_rules

    # Assert - IpRange nodes created
    ip_ranges = check_nodes(
        neo4j_session,
        "IpRange",
        ["id"],
    )
    assert ("0.0.0.0/0",) in ip_ranges

    # Assert - IpRange to IpRule relationship (MEMBER_OF_IP_RULE)
    assert check_rels(
        neo4j_session,
        "IpRange",
        "id",
        "IpRule",
        "id",
        "MEMBER_OF_IP_RULE",
        rel_direction_right=True,
    )

    # Assert - IpRule to Firewall relationship (IpRule)-[ALLOWED_BY]->(GCPFirewall)
    allowed_by_rels = check_rels(
        neo4j_session,
        "IpRule",
        "id",
        "GCPFirewall",
        "id",
        "ALLOWED_BY",
        rel_direction_right=True,
    )
    # SSH rule should be allowed by the SSH firewall
    assert (
        "projects/project-abc/global/firewalls/default-allow-ssh/allow/22tcp",
        "projects/project-abc/global/firewalls/default-allow-ssh",
    ) in allowed_by_rels


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_firewall_ingress_rules",
    return_value=tests.data.gcp.compute.LIST_FIREWALLS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_firewall_rules_with_target_tags(
    mock_get_vpcs, mock_get_firewalls, neo4j_session
):
    """Test that firewalls with target tags create TARGET_TAG relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_firewall_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Firewall to NetworkTag TARGET_TAG relationship (custom-port-incoming has targetTags: ["test"])
    assert check_rels(
        neo4j_session,
        "GCPFirewall",
        "id",
        "GCPNetworkTag",
        "id",
        "TARGET_TAG",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/firewalls/custom-port-incoming",
            "projects/project-abc/global/networks/default/tags/test",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    side_effect=[
        tests.data.gcp.compute.VPC_RESPONSE,
        tests.data.gcp.compute.VPC_RESPONSE_2,
    ],
)
def test_cleanup_not_scoped_to_project(mock_get_vpcs, neo4j_session):
    """Test that cleanup removes VPCs from other projects because it is not scoped."""
    # Arrange
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "PROJECT_ID": "project-abc"}
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Create projects
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId="project-abc",
        gcp_update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId="project-def",
        gcp_update_tag=TEST_UPDATE_TAG,
    )

    # First sync for project-abc
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        "project-abc",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert that the first project->vpc rel is created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpc",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("project-abc", "projects/project-abc/global/networks/default"),
    }, "First project->vpc rels is not created"

    # Act: sync the second project at a later time
    new_tag = TEST_UPDATE_TAG + 1
    common_job_parameters["UPDATE_TAG"] = new_tag
    common_job_parameters["PROJECT_ID"] = "project-def"
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        "project-def",
        new_tag,
        common_job_parameters,
    )

    # Assert that the second project->vpc rel is created and the first project->vpc rel remains
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpc",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("project-abc", "projects/project-abc/global/networks/default"),
        ("project-def", "projects/project-def/global/networks/default2"),
    }, "Second project->vpc rels are not created"
