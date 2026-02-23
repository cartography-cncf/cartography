"""
Tests for Azure compute asset exposure analysis jobs.

These tests verify that the analysis jobs correctly set exposed_internet properties
and create EXPOSE/PROTECTS relationships by building up the prerequisite graph state
and then running the analysis jobs against it.
"""

import cartography.util
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
}


def _create_base_graph(neo4j_session):
    """
    Create the base graph topology for exposure testing.

    Scenario 1 - Directly exposed VM (vm-direct):
        pip-direct <-[:ASSOCIATED_WITH]- nic-direct -[:ATTACHED_TO]-> vm-direct

    Scenario 2 - VM exposed via LB (vm-lb):
        pip-lb <-[:ASSOCIATED_WITH]- fip <-[:CONTAINS]- test-lb -[:CONTAINS]-> pool
            -[:ROUTES_TO]-> nic-lb -[:ATTACHED_TO]-> vm-lb

    Scenario 3 - Firewall protects LB (same VNet):
        test-fw -[:PART_OF_NETWORK]-> test-vnet -[:CONTAINS]-> default -[:CONTAINS]-> nic-lb

    Scenario 4 - Container instances:
        public-aci: has ip_address, no subnet
        private-aci: has ip_address, ATTACHED_TO container-subnet
    """
    neo4j_session.run(
        "MERGE (sub:AzureSubscription{id: $sub_id}) SET sub.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    # --- Scenario 1: Directly exposed VM ---
    neo4j_session.run(
        "MERGE (vm:AzureVirtualMachine{id: 'vm-direct-id'}) SET vm.name = 'vm-direct', vm.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (nic:AzureNetworkInterface{id: 'nic-direct-id'}) SET nic.name = 'nic-direct', nic.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (pip:AzurePublicIPAddress{id: 'pip-direct-id'}) SET pip.ip_address = '52.1.2.3', pip.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (nic:AzureNetworkInterface{id:'nic-direct-id'}), (vm:AzureVirtualMachine{id:'vm-direct-id'}) "
        "MERGE (nic)-[:ATTACHED_TO]->(vm)",
    )
    neo4j_session.run(
        "MATCH (nic:AzureNetworkInterface{id:'nic-direct-id'}), (pip:AzurePublicIPAddress{id:'pip-direct-id'}) "
        "MERGE (nic)-[:ASSOCIATED_WITH]->(pip)",
    )

    # --- Scenario 2: VM exposed via LB ---
    neo4j_session.run(
        "MERGE (vm:AzureVirtualMachine{id: 'vm-lb-id'}) SET vm.name = 'vm-lb', vm.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (nic:AzureNetworkInterface{id: 'nic-lb-id'}) SET nic.name = 'nic-lb', nic.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (nic:AzureNetworkInterface{id:'nic-lb-id'}), (vm:AzureVirtualMachine{id:'vm-lb-id'}) "
        "MERGE (nic)-[:ATTACHED_TO]->(vm)",
    )
    neo4j_session.run(
        "MERGE (lb:AzureLoadBalancer{id: 'test-lb-id'}) SET lb.name = 'test-lb', lb.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (fip:AzureLoadBalancerFrontendIPConfiguration{id: 'fip-id'}) SET fip.name = 'fip', fip.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (pip:AzurePublicIPAddress{id: 'pip-lb-id'}) SET pip.ip_address = '52.1.2.4', pip.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (bp:AzureLoadBalancerBackendPool{id: 'pool-id'}) SET bp.name = 'pool', bp.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (lb:AzureLoadBalancer{id:'test-lb-id'}), (fip:AzureLoadBalancerFrontendIPConfiguration{id:'fip-id'}) "
        "MERGE (lb)-[:CONTAINS]->(fip)",
    )
    neo4j_session.run(
        "MATCH (lb:AzureLoadBalancer{id:'test-lb-id'}), (bp:AzureLoadBalancerBackendPool{id:'pool-id'}) "
        "MERGE (lb)-[:CONTAINS]->(bp)",
    )
    neo4j_session.run(
        "MATCH (fip:AzureLoadBalancerFrontendIPConfiguration{id:'fip-id'}), (pip:AzurePublicIPAddress{id:'pip-lb-id'}) "
        "MERGE (fip)-[:ASSOCIATED_WITH]->(pip)",
    )
    neo4j_session.run(
        "MATCH (bp:AzureLoadBalancerBackendPool{id:'pool-id'}), (nic:AzureNetworkInterface{id:'nic-lb-id'}) "
        "MERGE (bp)-[:ROUTES_TO]->(nic)",
    )
    neo4j_session.run(
        "MATCH (sub:AzureSubscription{id:$sub_id}), (lb:AzureLoadBalancer{id:'test-lb-id'}) "
        "MERGE (sub)-[:RESOURCE]->(lb)",
        sub_id=TEST_SUBSCRIPTION_ID,
    )

    # --- Scenario 3: Firewall protects LB (same VNet) ---
    neo4j_session.run(
        "MERGE (fw:AzureFirewall{id: 'test-fw-id'}) SET fw.name = 'test-fw', fw.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (vnet:AzureVirtualNetwork{id: 'test-vnet-id'}) SET vnet.name = 'test-vnet', vnet.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sn:AzureSubnet{id: 'default-subnet-id'}) SET sn.name = 'default', sn.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (sub:AzureSubscription{id:$sub_id}), (fw:AzureFirewall{id:'test-fw-id'}) "
        "MERGE (sub)-[:RESOURCE]->(fw)",
        sub_id=TEST_SUBSCRIPTION_ID,
    )
    neo4j_session.run(
        "MATCH (fw:AzureFirewall{id:'test-fw-id'}), (vnet:AzureVirtualNetwork{id:'test-vnet-id'}) "
        "MERGE (fw)-[:MEMBER_OF]->(vnet)",
    )
    neo4j_session.run(
        "MATCH (vnet:AzureVirtualNetwork{id:'test-vnet-id'}), (sn:AzureSubnet{id:'default-subnet-id'}) "
        "MERGE (vnet)-[:CONTAINS]->(sn)",
    )
    neo4j_session.run(
        "MATCH (nic:AzureNetworkInterface{id:'nic-lb-id'}), (sn:AzureSubnet{id:'default-subnet-id'}) "
        "MERGE (nic)-[:ATTACHED_TO]->(sn)",
    )

    # --- Scenario 4: Container instances ---
    neo4j_session.run(
        "MERGE (c:AzureContainerInstance:Container{id: 'public-aci-id'}) "
        "SET c.name = 'public-aci', c.ip_address = '20.1.2.3', c.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (c:AzureContainerInstance:Container{id: 'private-aci-id'}) "
        "SET c.name = 'private-aci', c.ip_address = '10.0.1.5', c.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sn:AzureSubnet{id: 'container-subnet-id'}) SET sn.name = 'container-subnet', sn.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (c:AzureContainerInstance{id:'private-aci-id'}), (sn:AzureSubnet{id:'container-subnet-id'}) "
        "MERGE (c)-[:ATTACHED_TO]->(sn)",
    )


def test_azure_compute_exposure_end_to_end(neo4j_session):
    """
    End-to-end test that runs all three Azure compute exposure analysis jobs
    and verifies the resulting exposed_internet properties and EXPOSE/PROTECTS relationships.
    """
    # Arrange
    _create_base_graph(neo4j_session)

    # Act: Run all three analysis jobs in order
    cartography.util.run_analysis_job(
        "azure_compute_asset_exposure.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )
    cartography.util.run_scoped_analysis_job(
        "azure_lb_exposure.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )
    cartography.util.run_scoped_analysis_job(
        "azure_firewall_lb_protection.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )

    # Assert: exposed_internet on VMs
    assert check_nodes(
        neo4j_session,
        "AzureVirtualMachine",
        ["id", "exposed_internet"],
    ) == {
        ("vm-direct-id", True),
        ("vm-lb-id", True),
    }

    # Assert: exposed_internet on LBs
    assert check_nodes(
        neo4j_session,
        "AzureLoadBalancer",
        ["id", "exposed_internet"],
    ) == {
        ("test-lb-id", True),
    }

    # Assert: exposed_internet on containers
    assert check_nodes(
        neo4j_session,
        "AzureContainerInstance",
        ["id", "exposed_internet"],
    ) == {
        ("public-aci-id", True),
        ("private-aci-id", False),
    }

    # Assert: EXPOSE relationship from LB to private VM
    assert check_rels(
        neo4j_session,
        "AzureLoadBalancer",
        "id",
        "AzureVirtualMachine",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {("test-lb-id", "vm-lb-id")}

    # Assert: PROTECTS relationship from firewall to LB
    assert check_rels(
        neo4j_session,
        "AzureFirewall",
        "id",
        "AzureLoadBalancer",
        "id",
        "PROTECTS",
        rel_direction_right=True,
    ) == {("test-fw-id", "test-lb-id")}


def test_azure_lb_exposure_requires_compute_analysis_first(neo4j_session):
    """
    LB EXPOSE relationships depend on lb.exposed_internet, which is set by
    azure_compute_asset_exposure.json.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_base_graph(neo4j_session)

    # Running scoped LB exposure before compute analysis should not create EXPOSE rels.
    cartography.util.run_scoped_analysis_job(
        "azure_lb_exposure.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )
    assert (
        check_rels(
            neo4j_session,
            "AzureLoadBalancer",
            "id",
            "AzureVirtualMachine",
            "id",
            "EXPOSE",
            rel_direction_right=True,
        )
        == set()
    )

    # After compute analysis, scoped LB exposure should create EXPOSE rels.
    cartography.util.run_analysis_job(
        "azure_compute_asset_exposure.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )
    cartography.util.run_scoped_analysis_job(
        "azure_lb_exposure.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )
    assert check_rels(
        neo4j_session,
        "AzureLoadBalancer",
        "id",
        "AzureVirtualMachine",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {("test-lb-id", "vm-lb-id")}
