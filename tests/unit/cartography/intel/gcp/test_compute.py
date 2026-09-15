import cartography.intel.gcp.compute
from tests.data.gcp.compute import LIST_FIREWALLS_RESPONSE
from tests.data.gcp.compute import VPC_PEERING_RESPONSE
from tests.data.gcp.compute import VPC_RESPONSE
from tests.data.gcp.compute import VPC_SUBNET_RESPONSE
from tests.data.gcp.compute import VPN_GATEWAYS_RESPONSE
from tests.data.gcp.compute import VPN_TUNNELS_RESPONSE


def test_transform_gcp_vpcs():
    """
    Ensure that transform_gcp_vpcs() returns a list of VPCs, computes correct partial_uris, and parses the nested
    objects correctly.
    """
    vpc_list = cartography.intel.gcp.compute.transform_gcp_vpcs(VPC_RESPONSE)
    assert len(vpc_list) == 1

    vpc = vpc_list[0]
    assert vpc["partial_uri"] == "projects/project-abc/global/networks/default"
    assert vpc["routing_config_routing_mode"] == "REGIONAL"


def test_transform_gcp_subnets():
    """
    Ensure that transform_gcp_subnets() returns a list of subnets with correct partial_uris and tests for the presence
    of some key members.
    """
    subnet_list = cartography.intel.gcp.compute.transform_gcp_subnets(
        VPC_SUBNET_RESPONSE,
    )
    assert len(subnet_list) == 1

    subnet = subnet_list[0]
    assert subnet["ip_cidr_range"] == "10.0.0.0/20"
    assert (
        subnet["partial_uri"]
        == "projects/project-abc/regions/europe-west2/subnetworks/default"
    )
    assert subnet["region"] == "europe-west2"
    assert not subnet["private_ip_google_access"]


def test_parse_compute_full_uri_to_partial_uri():
    subnet_uri = "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default"
    inst_uri = "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1"
    vpc_uri = "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default"

    assert (
        cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(subnet_uri)
        == "projects/project-abc/regions/europe-west2/subnetworks/default"
    )
    assert (
        cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(inst_uri)
        == "projects/project-abc/zones/europe-west2-b/disks/instance-1"
    )
    assert (
        cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(vpc_uri)
        == "projects/project-abc/global/networks/default"
    )


def test_zones_to_regions():
    """
    Ensure that _zones_to_regions() correctly extracts regions from zones using
    the region URL rather than parsing zone names. This is important for
    non-standard zone names like AI zones (e.g., us-south1-ai).
    """
    # Standard zones
    standard_zones = [
        {
            "name": "us-central1-a",
            "region": "https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1",
        },
        {
            "name": "us-central1-b",
            "region": "https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1",
        },
        {
            "name": "europe-west1-b",
            "region": "https://www.googleapis.com/compute/v1/projects/my-project/regions/europe-west1",
        },
    ]
    result = cartography.intel.gcp.compute._zones_to_regions(standard_zones)
    assert sorted(result) == ["europe-west1", "us-central1"]

    # AI zones - these have non-standard zone names that would fail with the old
    # implementation that simply chopped off the last 2 characters
    ai_zones = [
        {
            "name": "us-south1-ai",
            "region": "https://www.googleapis.com/compute/v1/projects/my-project/regions/us-south1",
        },
        {
            "name": "us-central1-a",
            "region": "https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1",
        },
    ]
    result = cartography.intel.gcp.compute._zones_to_regions(ai_zones)
    # Should correctly extract us-south1, not us-south1-ai or us-south1-
    assert sorted(result) == ["us-central1", "us-south1"]


def test_transform_gcp_firewall():
    fw_list = cartography.intel.gcp.compute.transform_gcp_firewall(
        LIST_FIREWALLS_RESPONSE,
    )

    # Default-allow-internal
    sample_fw = fw_list[1]
    assert len(sample_fw["transformed_deny_list"]) == 0

    sample_udp_all_rule = sample_fw["transformed_allow_list"][1]

    assert sample_udp_all_rule["protocol"] == "udp"
    assert sample_udp_all_rule["fromport"] == 0
    assert sample_udp_all_rule["toport"] == 65535

    sample_fw_icmp_rule = sample_fw["transformed_allow_list"][2]
    assert sample_fw_icmp_rule["protocol"] == "icmp"
    assert sample_fw_icmp_rule["fromport"] is None
    assert sample_fw_icmp_rule["toport"] is None
    assert sample_fw_icmp_rule["protocol"] == "icmp"


def test_transform_gcp_vpc_peerings():
    """
    Ensure that transform_gcp_vpc_peerings() extracts peerings from a
    networks.list response, builds stable IDs, and parses peer project IDs.
    """
    peerings = cartography.intel.gcp.compute.transform_gcp_vpc_peerings(
        VPC_PEERING_RESPONSE
    )
    assert len(peerings) == 2

    peering = peerings[0]
    assert (
        peering["id"]
        == "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-b"
    )
    assert peering["network_partial_uri"] == (
        "projects/project-abc/global/networks/vpc-a"
    )
    assert peering["peer_network_partial_uri"] == (
        "projects/project-def/global/networks/vpc-b"
    )
    assert peering["peer_project_id"] == "project-def"
    assert peering["state"] == "ACTIVE"
    assert peering["peer_mtu"] == 1460
    assert peering["export_custom_routes"] is True
    assert peering["import_custom_routes"] is False

    peering2 = peerings[1]
    assert peering2["peer_project_id"] == "project-xyz"


def test_transform_gcp_vpc_peerings_no_peerings():
    """
    Ensure that transform_gcp_vpc_peerings() returns an empty list when no
    network has peerings.
    """
    assert cartography.intel.gcp.compute.transform_gcp_vpc_peerings(VPC_RESPONSE) == []


def test_transform_gcp_vpn_gateways():
    """
    Ensure that transform_gcp_vpn_gateways() builds correct partial URIs and
    parses the network reference.
    """
    gateways = cartography.intel.gcp.compute.transform_gcp_vpn_gateways(
        VPN_GATEWAYS_RESPONSE["items"],
        "project-abc",
    )
    assert len(gateways) == 1

    gateway = gateways[0]
    assert (
        gateway["partial_uri"]
        == "projects/project-abc/regions/us-central1/vpnGateways/gw-a"
    )
    assert gateway["project_id"] == "project-abc"
    assert gateway["region"] == "us-central1"
    assert gateway["network_partial_uri"] == (
        "projects/project-abc/global/networks/vpc-a"
    )
    assert gateway["gateway_ip_version"] == "IPV4"


def test_transform_gcp_vpn_tunnels():
    """
    Ensure that transform_gcp_vpn_tunnels() builds correct partial URIs, parses
    gateway references, and never copies the shared secret fields.
    """
    tunnels = cartography.intel.gcp.compute.transform_gcp_vpn_tunnels(
        VPN_TUNNELS_RESPONSE["items"],
        "project-abc",
    )
    assert len(tunnels) == 3

    tunnel = tunnels[0]
    assert (
        tunnel["partial_uri"]
        == "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-b"
    )
    assert tunnel["vpn_gateway_partial_uri"] == (
        "projects/project-abc/regions/us-central1/vpnGateways/gw-a"
    )
    assert tunnel["peer_gcp_gateway_partial_uri"] == (
        "projects/project-def/regions/us-central1/vpnGateways/gw-b"
    )
    assert tunnel["target_vpn_gateway_partial_uri"] is None
    assert tunnel["status"] == "ESTABLISHED"

    classic = tunnels[2]
    assert classic["vpn_gateway_partial_uri"] is None
    assert classic["peer_gcp_gateway_partial_uri"] is None
    assert classic["target_vpn_gateway_partial_uri"] == (
        "projects/project-abc/regions/us-central1/targetVpnGateways/classic-gw"
    )
    assert classic["peer_ip"] == "198.51.100.1"

    # sharedSecret / sharedSecretHash must never be copied to the graph.
    for t in tunnels:
        assert "sharedSecret" not in t
        assert "sharedSecretHash" not in t
        assert "shared_secret" not in t
