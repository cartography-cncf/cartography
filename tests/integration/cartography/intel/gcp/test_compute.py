import cartography.intel.gcp.compute
import tests.data.gcp.compute

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_instance_data(neo4j_session):
    cartography.intel.gcp.compute.load_gcp_instances(
        neo4j_session,
        tests.data.gcp.compute.TRANSFORMED_GCP_INSTANCES,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_vpc_data(neo4j_session):
    cartography.intel.gcp.compute.load_gcp_vpcs(
        neo4j_session,
        tests.data.gcp.compute.TRANSFORMED_GCP_VPCS,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_subnet_data(neo4j_session):
    cartography.intel.gcp.compute.load_gcp_subnets(
        neo4j_session,
        tests.data.gcp.compute.TRANSFORMED_GCP_SUBNETS,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_firewall_data(neo4j_session):
    cartography.intel.gcp.compute.load_gcp_ingress_firewalls(
        neo4j_session,
        tests.data.gcp.compute.TRANSFORMED_FW_LIST,
        TEST_UPDATE_TAG,
    )


def test_transform_and_load_vpcs(neo4j_session):
    """
    Test that we can correctly transform and load VPC nodes to Neo4j.
    """
    vpc_res = tests.data.gcp.compute.VPC_RESPONSE
    vpc_list = cartography.intel.gcp.compute.transform_gcp_vpcs(vpc_res)
    cartography.intel.gcp.compute.load_gcp_vpcs(
        neo4j_session,
        vpc_list,
        TEST_UPDATE_TAG,
    )

    query = """
    MATCH(vpc:GCPVpc{id:$VpcId})
    RETURN vpc.id, vpc.partial_uri, vpc.auto_create_subnetworks
    """
    expected_vpc_id = "projects/project-abc/global/networks/default"
    nodes = neo4j_session.run(
        query,
        VpcId=expected_vpc_id,
    )
    actual_nodes = {
        (n["vpc.id"], n["vpc.partial_uri"], n["vpc.auto_create_subnetworks"])
        for n in nodes
    }
    expected_nodes = {
        (expected_vpc_id, expected_vpc_id, True),
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_subnets(neo4j_session):
    """
    Ensure we can transform and load subnets.
    """
    subnet_res = tests.data.gcp.compute.VPC_SUBNET_RESPONSE
    subnet_list = cartography.intel.gcp.compute.transform_gcp_subnets(subnet_res)
    cartography.intel.gcp.compute.load_gcp_subnets(
        neo4j_session,
        subnet_list,
        TEST_UPDATE_TAG,
    )

    query = """
    MATCH(subnet:GCPSubnet)
    RETURN subnet.id, subnet.region, subnet.gateway_address, subnet.ip_cidr_range, subnet.private_ip_google_access,
    subnet.vpc_partial_uri
    """
    nodes = neo4j_session.run(query)
    actual_nodes = {
        (
            n["subnet.id"],
            n["subnet.region"],
            n["subnet.gateway_address"],
            n["subnet.ip_cidr_range"],
            n["subnet.private_ip_google_access"],
            n["subnet.vpc_partial_uri"],
        )
        for n in nodes
    }

    expected_nodes = {
        (
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "europe-west2",
            "10.0.0.1",
            "10.0.0.0/20",
            False,
            "projects/project-abc/global/networks/default",
        ),
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_gcp_forwarding_rules(neo4j_session):
    """
    Ensure that we can correctly transform and load GCP Forwarding Rules
    """
    fwd_res = tests.data.gcp.compute.LIST_FORWARDING_RULES_RESPONSE
    fwd_list = cartography.intel.gcp.compute.transform_gcp_forwarding_rules(fwd_res)
    cartography.intel.gcp.compute.load_gcp_forwarding_rules(
        neo4j_session,
        fwd_list,
        TEST_UPDATE_TAG,
    )

    fwd_query = """
    MATCH(f:GCPForwardingRule)
    RETURN f.id, f.partial_uri, f.ip_address, f.ip_protocol, f.load_balancing_scheme, f.name, f.network, f.port_range,
    f.ports, f.project_id, f.region, f.self_link, f.subnetwork, f.target
    """
    objects = neo4j_session.run(fwd_query)
    actual_nodes = {
        (
            o["f.id"],
            o["f.ip_address"],
            o["f.ip_protocol"],
            o["f.load_balancing_scheme"],
            o["f.name"],
            o.get("f.port_range", None),
            ",".join(o.get("f.ports", None)) if o.get("f.ports", None) else None,
            o["f.project_id"],
            o["f.region"],
            o["f.target"],
        )
        for o in objects
    }

    expected_nodes = {
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-service-1111",
            "10.0.0.10",
            "TCP",
            "INTERNAL",
            "internal-service-1111",
            None,
            "80",
            "project-abc",
            "europe-west2",
            "projects/project-abc/regions/europe-west2/targetPools/node-pool-12345",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/public-ingress-controller-1234567",
            "1.2.3.11",
            "TCP",
            "EXTERNAL",
            "public-ingress-controller-1234567",
            "80-443",
            None,
            "project-abc",
            "europe-west2",
            "projects/project-abc/regions/europe-west2/targetVpnGateways/vpn-12345",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/shard-server-22222",
            "10.0.0.20",
            "TCP",
            "INTERNAL",
            "shard-server-22222",
            None,
            "10203",
            "project-abc",
            "europe-west2",
            "projects/project-abc/regions/europe-west2/targetPools/node-pool-234567",
        ),
    }

    assert actual_nodes == expected_nodes


def test_transform_and_load_gcp_instances_and_nics(neo4j_session):
    """
    Ensure that we can correctly transform and load GCP instances.
    """
    instance_responses = [tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE]
    instance_list = cartography.intel.gcp.compute.transform_gcp_instances(
        instance_responses,
    )
    cartography.intel.gcp.compute.load_gcp_instances(
        neo4j_session,
        instance_list,
        TEST_UPDATE_TAG,
    )

    instance_id1 = "projects/project-abc/zones/europe-west2-b/instances/instance-1-test"
    instance_id2 = "projects/project-abc/zones/europe-west2-b/instances/instance-1"

    nic_query = """
    MATCH(i:GCPInstance)-[r:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
    OPTIONAL MATCH (i)-[:TAGGED]->(t:GCPNetworkTag)
    RETURN i.id, i.zone_name, i.project_id, i.hostname, t.value, r.lastupdated, nic.nic_id, nic.private_ip
    """
    objects = neo4j_session.run(nic_query)
    actual_nodes = {
        (
            o["i.id"],
            o["i.zone_name"],
            o["i.project_id"],
            o["nic.nic_id"],
            o["nic.private_ip"],
            o["t.value"],
            o["r.lastupdated"],
        )
        for o in objects
    }

    expected_nodes = {
        (
            instance_id1,
            "europe-west2-b",
            "project-abc",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
            "10.0.0.3",
            None,
            TEST_UPDATE_TAG,
        ),
        (
            instance_id2,
            "europe-west2-b",
            "project-abc",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
            "10.0.0.2",
            "test",
            TEST_UPDATE_TAG,
        ),
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_firewalls(neo4j_session):
    """
    Ensure we can correctly transform and load GCP firewalls
    :param neo4j_session:
    :return:
    """
    fw_list = cartography.intel.gcp.compute.transform_gcp_firewall(
        tests.data.gcp.compute.LIST_FIREWALLS_RESPONSE,
    )
    cartography.intel.gcp.compute.load_gcp_ingress_firewalls(
        neo4j_session,
        fw_list,
        TEST_UPDATE_TAG,
    )

    query = """
    MATCH (vpc:GCPVpc)-[r:RESOURCE]->(fw:GCPFirewall)
    return vpc.id, fw.id, fw.has_target_service_accounts
    """

    nodes = neo4j_session.run(query)
    actual_nodes = {
        (
            (
                n["vpc.id"],
                n["fw.id"],
                n["fw.has_target_service_accounts"],
            )
        )
        for n in nodes
    }
    expected_nodes = {
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-icmp",
            False,
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-internal",
            False,
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-rdp",
            False,
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-ssh",
            False,
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/custom-port-incoming",
            False,
        ),
    }
    assert actual_nodes == expected_nodes


def test_vpc_to_subnets(neo4j_session):
    """
    Ensure that subnets are connected to VPCs.
    """
    _ensure_local_neo4j_has_test_vpc_data(neo4j_session)
    _ensure_local_neo4j_has_test_subnet_data(neo4j_session)
    query = """
    MATCH(vpc:GCPVpc{id:$VpcId})-[:RESOURCE]->(subnet:GCPSubnet)
    RETURN vpc.id, subnet.id, subnet.region, subnet.gateway_address, subnet.ip_cidr_range,
    subnet.private_ip_google_access
    """
    expected_vpc_id = "projects/project-abc/global/networks/default"
    nodes = neo4j_session.run(
        query,
        VpcId=expected_vpc_id,
    )
    actual_nodes = {
        (
            n["vpc.id"],
            n["subnet.id"],
            n["subnet.region"],
            n["subnet.gateway_address"],
            n["subnet.ip_cidr_range"],
            n["subnet.private_ip_google_access"],
        )
        for n in nodes
    }

    expected_nodes = {
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "europe-west2",
            "10.0.0.1",
            "10.0.0.0/20",
            False,
        ),
    }
    assert actual_nodes == expected_nodes


def test_nics_to_access_configs(neo4j_session):
    """
    Ensure that network interfaces and access configs are attached
    """
    _ensure_local_neo4j_has_test_instance_data(neo4j_session)
    ac_query = """
    MATCH (nic:GCPNetworkInterface)-[r:RESOURCE]->(ac:GCPNicAccessConfig)
    return nic.nic_id, ac.access_config_id, ac.public_ip
    """
    nodes = neo4j_session.run(ac_query)

    nic_id1 = "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0"
    ac_id1 = f"{nic_id1}/accessconfigs/ONE_TO_ONE_NAT"
    nic_id2 = "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0"
    ac_id2 = f"{nic_id2}/accessconfigs/ONE_TO_ONE_NAT"

    actual_nodes = {
        (n["nic.nic_id"], n["ac.access_config_id"], n["ac.public_ip"]) for n in nodes
    }
    expected_nodes = {
        (nic_id1, ac_id1, "1.3.4.5"),
        (nic_id2, ac_id2, "1.2.3.4"),
    }
    assert actual_nodes == expected_nodes


def test_nic_to_subnets(neo4j_session):
    """
    Ensure that network interfaces are attached to subnets
    """
    _ensure_local_neo4j_has_test_subnet_data(neo4j_session)
    _ensure_local_neo4j_has_test_instance_data(neo4j_session)
    subnet_query = """
    MATCH (nic:GCPNetworkInterface{id:$NicId})-[:PART_OF_SUBNET]->(subnet:GCPSubnet)
    return nic.nic_id, nic.private_ip, subnet.id, subnet.gateway_address, subnet.ip_cidr_range
    """
    nodes = neo4j_session.run(
        subnet_query,
        NicId="projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
    )
    actual_nodes = {
        (
            n["nic.nic_id"],
            n["nic.private_ip"],
            n["subnet.id"],
            n["subnet.gateway_address"],
            n["subnet.ip_cidr_range"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
            "10.0.0.3",
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "10.0.0.1",
            "10.0.0.0/20",
        ),
    }
    assert actual_nodes == expected_nodes


def test_instance_to_vpc(neo4j_session):
    _ensure_local_neo4j_has_test_vpc_data(neo4j_session)
    _ensure_local_neo4j_has_test_subnet_data(neo4j_session)
    _ensure_local_neo4j_has_test_instance_data(neo4j_session)
    instance_id1 = "projects/project-abc/zones/europe-west2-b/instances/instance-1-test"
    query = """
    MATCH (i:GCPInstance{id:$InstanceId})-[r:MEMBER_OF_GCP_VPC]->(v:GCPVpc)
    RETURN i.id, v.id
    """
    nodes = neo4j_session.run(
        query,
        InstanceId=instance_id1,
    )
    actual_nodes = {
        (
            n["i.id"],
            n["v.id"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            instance_id1,
            "projects/project-abc/global/networks/default",
        ),
    }
    assert actual_nodes == expected_nodes


def test_vpc_to_firewall_to_iprule_to_iprange(neo4j_session):
    _ensure_local_neo4j_has_test_vpc_data(neo4j_session)
    _ensure_local_neo4j_has_test_firewall_data(neo4j_session)
    query = """
    MATCH (rng:IpRange{id:'0.0.0.0/0'})-[m:MEMBER_OF_IP_RULE]->(rule:IpRule{fromport:22})
           -[a:ALLOWED_BY]->(fw:GCPFirewall)<-[r:RESOURCE]-(vpc:GCPVpc)
    RETURN rng.id, rule.id, fw.id, fw.priority, vpc.id
    """
    nodes = neo4j_session.run(query)
    actual_nodes = {
        (
            n["rng.id"],
            n["rule.id"],
            n["fw.id"],
            n["vpc.id"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            "0.0.0.0/0",
            "projects/project-abc/global/firewalls/default-allow-ssh/allow/22tcp",
            "projects/project-abc/global/firewalls/default-allow-ssh",
            "projects/project-abc/global/networks/default",
        ),
    }
    assert actual_nodes == expected_nodes
