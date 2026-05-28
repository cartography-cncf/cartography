# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Network API-centric functions
# https://docs.cloud.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm
import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


# ============================================================
# VCNs (Virtual Cloud Networks)
# ============================================================

def get_vcn_list_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all VCNs in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Vcn/ListVcns
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            network_client.list_vcns, compartment_id=compartment_id,
        )
        return {'Vcns': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve VCNs for compartment '%s': %s", compartment_id, e.message,
        )
        return {'Vcns': []}


def load_vcns(
    neo4j_session: neo4j.Session,
    vcns: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI VCN data into Neo4j.
    """
    ingest_vcn = """
    MERGE (vcn:OCIVcn{ocid: $OCID})
    ON CREATE SET vcn.firstseen = timestamp(),
    vcn.createdate = $TIME_CREATED
    SET vcn.display_name = $DISPLAY_NAME,
    vcn.compartment_id = $COMPARTMENT_ID,
    vcn.cidr_block = $CIDR_BLOCK,
    vcn.dns_label = $DNS_LABEL,
    vcn.lifecycle_state = $LIFECYCLE_STATE,
    vcn.region = $REGION,
    vcn.lastupdated = $oci_update_tag
    WITH vcn
    MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(vcn)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for vcn in vcns:
        neo4j_session.run(
            ingest_vcn,
            OCID=vcn.get("id"),
            DISPLAY_NAME=vcn.get("display-name"),
            COMPARTMENT_ID=vcn.get("compartment-id", compartment_id),
            CIDR_BLOCK=vcn.get("cidr-block", ""),
            DNS_LABEL=vcn.get("dns-label", ""),
            LIFECYCLE_STATE=vcn.get("lifecycle-state"),
            REGION=region,
            TIME_CREATED=str(vcn.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_vcns(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all VCNs across compartments.
    """
    logger.debug("Syncing OCI VCNs for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_vcn_list_data(network_client, compartment["ocid"])
        if data["Vcns"]:
            load_vcns(neo4j_session, data["Vcns"], tenancy_id, compartment["ocid"], region, oci_update_tag)


# ============================================================
# Subnets
# ============================================================

def get_subnet_list_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all subnets in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Subnet/ListSubnets
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            network_client.list_subnets, compartment_id=compartment_id,
        )
        return {'Subnets': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve subnets for compartment '%s': %s", compartment_id, e.message,
        )
        return {'Subnets': []}


def load_subnets(
    neo4j_session: neo4j.Session,
    subnets: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Subnet data into Neo4j and link to VCN.
    """
    ingest_subnet = """
    MERGE (subnet:OCISubnet{ocid: $OCID})
    ON CREATE SET subnet.firstseen = timestamp(),
    subnet.createdate = $TIME_CREATED
    SET subnet.display_name = $DISPLAY_NAME,
    subnet.compartment_id = $COMPARTMENT_ID,
    subnet.cidr_block = $CIDR_BLOCK,
    subnet.availability_domain = $AVAILABILITY_DOMAIN,
    subnet.dns_label = $DNS_LABEL,
    subnet.lifecycle_state = $LIFECYCLE_STATE,
    subnet.vcn_id = $VCN_ID,
    subnet.route_table_id = $ROUTE_TABLE_ID,
    subnet.subnet_domain_name = $SUBNET_DOMAIN_NAME,
    subnet.prohibit_public_ip_on_vnic = $PROHIBIT_PUBLIC_IP,
    subnet.region = $REGION,
    subnet.lastupdated = $oci_update_tag
    WITH subnet
    MATCH (vcn:OCIVcn{ocid: $VCN_ID})
    MERGE (vcn)-[r:OCI_SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for subnet in subnets:
        neo4j_session.run(
            ingest_subnet,
            OCID=subnet.get("id"),
            DISPLAY_NAME=subnet.get("display-name"),
            COMPARTMENT_ID=subnet.get("compartment-id", compartment_id),
            CIDR_BLOCK=subnet.get("cidr-block", ""),
            AVAILABILITY_DOMAIN=subnet.get("availability-domain", ""),
            DNS_LABEL=subnet.get("dns-label", ""),
            LIFECYCLE_STATE=subnet.get("lifecycle-state"),
            VCN_ID=subnet.get("vcn-id", ""),
            ROUTE_TABLE_ID=subnet.get("route-table-id", ""),
            SUBNET_DOMAIN_NAME=subnet.get("subnet-domain-name", ""),
            PROHIBIT_PUBLIC_IP=subnet.get("prohibit-public-ip-on-vnic", False),
            REGION=region,
            TIME_CREATED=str(subnet.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_subnets(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all subnets across compartments.
    """
    logger.debug("Syncing OCI subnets for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_subnet_list_data(network_client, compartment["ocid"])
        if data["Subnets"]:
            load_subnets(neo4j_session, data["Subnets"], tenancy_id, compartment["ocid"], region, oci_update_tag)


# ============================================================
# Security Lists
# ============================================================

def get_security_list_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all security lists in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/SecurityList/ListSecurityLists
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            network_client.list_security_lists, compartment_id=compartment_id,
        )
        return {'SecurityLists': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve security lists for compartment '%s': %s", compartment_id, e.message,
        )
        return {'SecurityLists': []}


def load_security_lists(
    neo4j_session: neo4j.Session,
    security_lists: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Security List data into Neo4j and link to VCN.
    """
    ingest_security_list = """
    MERGE (sl:OCISecurityList{ocid: $OCID})
    ON CREATE SET sl.firstseen = timestamp(),
    sl.createdate = $TIME_CREATED
    SET sl.display_name = $DISPLAY_NAME,
    sl.compartment_id = $COMPARTMENT_ID,
    sl.vcn_id = $VCN_ID,
    sl.lifecycle_state = $LIFECYCLE_STATE,
    sl.ingress_security_rules = $INGRESS_RULES,
    sl.egress_security_rules = $EGRESS_RULES,
    sl.region = $REGION,
    sl.lastupdated = $oci_update_tag
    WITH sl
    MATCH (vcn:OCIVcn{ocid: $VCN_ID})
    MERGE (vcn)-[r:OCI_SECURITY_LIST]->(sl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for sl in security_lists:
        ingress_rules = sl.get("ingress-security-rules", [])
        egress_rules = sl.get("egress-security-rules", [])
        neo4j_session.run(
            ingest_security_list,
            OCID=sl.get("id"),
            DISPLAY_NAME=sl.get("display-name"),
            COMPARTMENT_ID=sl.get("compartment-id", compartment_id),
            VCN_ID=sl.get("vcn-id", ""),
            LIFECYCLE_STATE=sl.get("lifecycle-state"),
            INGRESS_RULES=json.dumps(ingress_rules) if ingress_rules else "[]",
            EGRESS_RULES=json.dumps(egress_rules) if egress_rules else "[]",
            REGION=region,
            TIME_CREATED=str(sl.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_security_lists(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all security lists across compartments.
    """
    logger.debug("Syncing OCI security lists for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_security_list_data(network_client, compartment["ocid"])
        if data["SecurityLists"]:
            load_security_lists(
                neo4j_session, data["SecurityLists"], tenancy_id, compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Network Security Groups (NSGs)
# ============================================================

def get_network_security_group_list_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all Network Security Groups in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/NetworkSecurityGroup/ListNetworkSecurityGroups
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            network_client.list_network_security_groups, compartment_id=compartment_id,
        )
        return {'NetworkSecurityGroups': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve NSGs for compartment '%s': %s", compartment_id, e.message,
        )
        return {'NetworkSecurityGroups': []}


def load_network_security_groups(
    neo4j_session: neo4j.Session,
    nsgs: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Network Security Group data into Neo4j and link to VCN.
    """
    ingest_nsg = """
    MERGE (nsg:OCINetworkSecurityGroup{ocid: $OCID})
    ON CREATE SET nsg.firstseen = timestamp(),
    nsg.createdate = $TIME_CREATED
    SET nsg.display_name = $DISPLAY_NAME,
    nsg.compartment_id = $COMPARTMENT_ID,
    nsg.vcn_id = $VCN_ID,
    nsg.lifecycle_state = $LIFECYCLE_STATE,
    nsg.region = $REGION,
    nsg.lastupdated = $oci_update_tag
    WITH nsg
    MATCH (vcn:OCIVcn{ocid: $VCN_ID})
    MERGE (vcn)-[r:OCI_NETWORK_SECURITY_GROUP]->(nsg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for nsg in nsgs:
        neo4j_session.run(
            ingest_nsg,
            OCID=nsg.get("id"),
            DISPLAY_NAME=nsg.get("display-name"),
            COMPARTMENT_ID=nsg.get("compartment-id", compartment_id),
            VCN_ID=nsg.get("vcn-id", ""),
            LIFECYCLE_STATE=nsg.get("lifecycle-state"),
            REGION=region,
            TIME_CREATED=str(nsg.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_network_security_groups(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all Network Security Groups across compartments.
    """
    logger.debug("Syncing OCI NSGs for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_network_security_group_list_data(network_client, compartment["ocid"])
        if data["NetworkSecurityGroups"]:
            load_network_security_groups(
                neo4j_session, data["NetworkSecurityGroups"], tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# NSG Security Rules
# ============================================================

def get_nsg_security_rules_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    nsg_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all security rules for a given Network Security Group.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/SecurityRule/ListNetworkSecurityGroupSecurityRules
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            network_client.list_network_security_group_security_rules,
            nsg_id,
        )
        return {'SecurityRules': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve NSG security rules for NSG '%s': %s", nsg_id, e.message,
        )
        return {'SecurityRules': []}


def load_nsg_security_rules(
    neo4j_session: neo4j.Session,
    rules: List[Dict[str, Any]],
    nsg_id: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI NSG Security Rule data into Neo4j and link to NSG.
    """
    ingest_rule = """
    MERGE (rule:OCINsgSecurityRule{ocid: $OCID})
    ON CREATE SET rule.firstseen = timestamp()
    SET rule.direction = $DIRECTION,
    rule.protocol = $PROTOCOL,
    rule.description = $DESCRIPTION,
    rule.source = $SOURCE,
    rule.source_type = $SOURCE_TYPE,
    rule.destination = $DESTINATION,
    rule.destination_type = $DESTINATION_TYPE,
    rule.is_stateless = $IS_STATELESS,
    rule.is_valid = $IS_VALID,
    rule.tcp_dest_port_min = $TCP_DEST_PORT_MIN,
    rule.tcp_dest_port_max = $TCP_DEST_PORT_MAX,
    rule.tcp_src_port_min = $TCP_SRC_PORT_MIN,
    rule.tcp_src_port_max = $TCP_SRC_PORT_MAX,
    rule.udp_dest_port_min = $UDP_DEST_PORT_MIN,
    rule.udp_dest_port_max = $UDP_DEST_PORT_MAX,
    rule.icmp_type = $ICMP_TYPE,
    rule.icmp_code = $ICMP_CODE,
    rule.lastupdated = $oci_update_tag
    WITH rule
    MATCH (nsg:OCINetworkSecurityGroup{ocid: $NSG_ID})
    MERGE (nsg)-[r:OCI_NSG_RULE]->(rule)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for rule in rules:
        # Extract TCP options
        tcp_options = rule.get("tcp-options", {}) or {}
        tcp_dest_range = tcp_options.get("destination-port-range", {}) or {}
        tcp_src_range = tcp_options.get("source-port-range", {}) or {}

        # Extract UDP options
        udp_options = rule.get("udp-options", {}) or {}
        udp_dest_range = udp_options.get("destination-port-range", {}) or {}

        # Extract ICMP options
        icmp_options = rule.get("icmp-options", {}) or {}

        neo4j_session.run(
            ingest_rule,
            OCID=rule.get("id"),
            DIRECTION=rule.get("direction", ""),
            PROTOCOL=rule.get("protocol", ""),
            DESCRIPTION=rule.get("description", ""),
            SOURCE=rule.get("source", ""),
            SOURCE_TYPE=rule.get("source-type", ""),
            DESTINATION=rule.get("destination", ""),
            DESTINATION_TYPE=rule.get("destination-type", ""),
            IS_STATELESS=rule.get("is-stateless", False),
            IS_VALID=rule.get("is-valid", True),
            TCP_DEST_PORT_MIN=tcp_dest_range.get("min"),
            TCP_DEST_PORT_MAX=tcp_dest_range.get("max"),
            TCP_SRC_PORT_MIN=tcp_src_range.get("min"),
            TCP_SRC_PORT_MAX=tcp_src_range.get("max"),
            UDP_DEST_PORT_MIN=udp_dest_range.get("min"),
            UDP_DEST_PORT_MAX=udp_dest_range.get("max"),
            ICMP_TYPE=icmp_options.get("type"),
            ICMP_CODE=icmp_options.get("code"),
            NSG_ID=nsg_id,
            oci_update_tag=oci_update_tag,
        )


def sync_nsg_security_rules(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all NSG security rules by querying existing NSGs from Neo4j
    and fetching rules for each.
    """
    logger.debug("Syncing OCI NSG security rules for tenancy '%s', region '%s'.", tenancy_id, region)
    compartment_ocid = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    query = (
        "MATCH (:OCICompartment{ocid: $COMPARTMENT_ID})-[:RESOURCE]->(:OCIVcn)"
        "-[:OCI_NETWORK_SECURITY_GROUP]->(nsg:OCINetworkSecurityGroup) "
        "WHERE nsg.region = $REGION "
        "RETURN nsg.ocid as ocid"
    )
    nsgs = neo4j_session.run(query, COMPARTMENT_ID=compartment_ocid, REGION=region)
    for nsg in nsgs:
        data = get_nsg_security_rules_data(network_client, nsg["ocid"])
        if data["SecurityRules"]:
            load_nsg_security_rules(neo4j_session, data["SecurityRules"], nsg["ocid"], oci_update_tag)


# ============================================================
# Internet Gateways
# ============================================================

def get_internet_gateway_list_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all internet gateways in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/InternetGateway/ListInternetGateways
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            network_client.list_internet_gateways, compartment_id=compartment_id,
        )
        return {'InternetGateways': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve internet gateways for compartment '%s': %s", compartment_id, e.message,
        )
        return {'InternetGateways': []}


def load_internet_gateways(
    neo4j_session: neo4j.Session,
    gateways: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Internet Gateway data into Neo4j and link to VCN.
    """
    ingest_igw = """
    MERGE (igw:OCIInternetGateway{ocid: $OCID})
    ON CREATE SET igw.firstseen = timestamp(),
    igw.createdate = $TIME_CREATED
    SET igw.display_name = $DISPLAY_NAME,
    igw.compartment_id = $COMPARTMENT_ID,
    igw.vcn_id = $VCN_ID,
    igw.is_enabled = $IS_ENABLED,
    igw.lifecycle_state = $LIFECYCLE_STATE,
    igw.region = $REGION,
    igw.lastupdated = $oci_update_tag
    WITH igw
    MATCH (vcn:OCIVcn{ocid: $VCN_ID})
    MERGE (vcn)-[r:OCI_INTERNET_GATEWAY]->(igw)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for gw in gateways:
        neo4j_session.run(
            ingest_igw,
            OCID=gw.get("id"),
            DISPLAY_NAME=gw.get("display-name"),
            COMPARTMENT_ID=gw.get("compartment-id", compartment_id),
            VCN_ID=gw.get("vcn-id", ""),
            IS_ENABLED=gw.get("is-enabled", True),
            LIFECYCLE_STATE=gw.get("lifecycle-state"),
            REGION=region,
            TIME_CREATED=str(gw.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_internet_gateways(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all internet gateways across compartments.
    """
    logger.debug("Syncing OCI internet gateways for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_internet_gateway_list_data(network_client, compartment["ocid"])
        if data["InternetGateways"]:
            load_internet_gateways(
                neo4j_session, data["InternetGateways"], tenancy_id, compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# NAT Gateways
# ============================================================

def get_nat_gateway_list_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all NAT gateways in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/NatGateway/ListNatGateways
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            network_client.list_nat_gateways, compartment_id=compartment_id,
        )
        return {'NatGateways': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve NAT gateways for compartment '%s': %s", compartment_id, e.message,
        )
        return {'NatGateways': []}


def load_nat_gateways(
    neo4j_session: neo4j.Session,
    gateways: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI NAT Gateway data into Neo4j and link to VCN.
    """
    ingest_nat = """
    MERGE (nat:OCINatGateway{ocid: $OCID})
    ON CREATE SET nat.firstseen = timestamp(),
    nat.createdate = $TIME_CREATED
    SET nat.display_name = $DISPLAY_NAME,
    nat.compartment_id = $COMPARTMENT_ID,
    nat.vcn_id = $VCN_ID,
    nat.nat_ip = $NAT_IP,
    nat.block_traffic = $BLOCK_TRAFFIC,
    nat.lifecycle_state = $LIFECYCLE_STATE,
    nat.region = $REGION,
    nat.lastupdated = $oci_update_tag
    WITH nat
    MATCH (vcn:OCIVcn{ocid: $VCN_ID})
    MERGE (vcn)-[r:OCI_NAT_GATEWAY]->(nat)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for gw in gateways:
        neo4j_session.run(
            ingest_nat,
            OCID=gw.get("id"),
            DISPLAY_NAME=gw.get("display-name"),
            COMPARTMENT_ID=gw.get("compartment-id", compartment_id),
            VCN_ID=gw.get("vcn-id", ""),
            NAT_IP=gw.get("nat-ip", ""),
            BLOCK_TRAFFIC=gw.get("block-traffic", False),
            LIFECYCLE_STATE=gw.get("lifecycle-state"),
            REGION=region,
            TIME_CREATED=str(gw.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_nat_gateways(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all NAT gateways across compartments.
    """
    logger.debug("Syncing OCI NAT gateways for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_nat_gateway_list_data(network_client, compartment["ocid"])
        if data["NatGateways"]:
            load_nat_gateways(
                neo4j_session, data["NatGateways"], tenancy_id, compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Route Tables
# ============================================================

def get_route_table_list_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all route tables in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/RouteTable/ListRouteTables
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            network_client.list_route_tables, compartment_id=compartment_id,
        )
        return {'RouteTables': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve route tables for compartment '%s': %s", compartment_id, e.message,
        )
        return {'RouteTables': []}


def load_route_tables(
    neo4j_session: neo4j.Session,
    route_tables: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Route Table data into Neo4j and link to VCN.
    """
    ingest_rt = """
    MERGE (rt:OCIRouteTable{ocid: $OCID})
    ON CREATE SET rt.firstseen = timestamp(),
    rt.createdate = $TIME_CREATED
    SET rt.display_name = $DISPLAY_NAME,
    rt.compartment_id = $COMPARTMENT_ID,
    rt.vcn_id = $VCN_ID,
    rt.lifecycle_state = $LIFECYCLE_STATE,
    rt.route_rules = $ROUTE_RULES,
    rt.region = $REGION,
    rt.lastupdated = $oci_update_tag
    WITH rt
    MATCH (vcn:OCIVcn{ocid: $VCN_ID})
    MERGE (vcn)-[r:OCI_ROUTE_TABLE]->(rt)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for rt in route_tables:
        route_rules = rt.get("route-rules", [])
        neo4j_session.run(
            ingest_rt,
            OCID=rt.get("id"),
            DISPLAY_NAME=rt.get("display-name"),
            COMPARTMENT_ID=rt.get("compartment-id", compartment_id),
            VCN_ID=rt.get("vcn-id", ""),
            LIFECYCLE_STATE=rt.get("lifecycle-state"),
            ROUTE_RULES=json.dumps(route_rules) if route_rules else "[]",
            REGION=region,
            TIME_CREATED=str(rt.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_route_tables(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all route tables across compartments.
    """
    logger.debug("Syncing OCI route tables for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_route_table_list_data(network_client, compartment["ocid"])
        if data["RouteTables"]:
            load_route_tables(
                neo4j_session, data["RouteTables"], tenancy_id, compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Top-level sync function
# ============================================================

def sync(
    neo4j_session: neo4j.Session,
    network: oci.core.virtual_network_client.VirtualNetworkClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str] = None,
) -> None:
    """
    Sync OCI Network resources for the compartment specified in common_job_parameters.
    """
    compartment_ocid = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI Network for compartment '%s'.", compartment_ocid)

    # Use only the target compartment for resource listing
    compartments = [{"ocid": compartment_ocid, "name": "target", "compartmentid": tenancy_id}]

    # If no regions provided, use the network client's current region
    if not regions:
        regions = [network.base_client.region or ""]

    for region in regions:
        logger.info("Syncing OCI Network in region '%s' for compartment '%s'.", region, compartment_ocid)
        network.base_client.set_region(region)

        # Sync VCNs first (parent of all other network resources)
        sync_vcns(neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters)

        # Sync subnets (children of VCNs)
        sync_subnets(neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters)

        # Sync security lists (children of VCNs)
        sync_security_lists(
            neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

        # Sync Network Security Groups (children of VCNs)
        sync_network_security_groups(
            neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

        # Sync NSG security rules (children of NSGs)
        sync_nsg_security_rules(
            neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

        # Sync internet gateways (children of VCNs)
        sync_internet_gateways(
            neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

        # Sync NAT gateways (children of VCNs)
        sync_nat_gateways(
            neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

        # Sync route tables (children of VCNs)
        sync_route_tables(
            neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

    # Cleanup stale network nodes
    run_cleanup_job('oci_import_network_cleanup.json', neo4j_session, common_job_parameters)
