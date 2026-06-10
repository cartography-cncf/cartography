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
import oci.logging

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
    subnet.security_list_ids = $SECURITY_LIST_IDS,
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
            SECURITY_LIST_IDS=subnet.get("security-list-ids", []) or [],
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
# Subnet associations (Subnet -> RouteTable, Subnet -> SecurityList)
# ============================================================

def sync_subnet_associations(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Link subnets to the route tables and security lists they reference. The IDs are
    captured on the OCISubnet node by load_subnets (route_table_id, security_list_ids).
    """
    logger.debug("Syncing OCI subnet associations for tenancy '%s', region '%s'.", tenancy_id, region)
    link_subnet_route_table = """
    MATCH (subnet:OCISubnet{ocid: $SUBNET_ID})
    MATCH (rt:OCIRouteTable{ocid: $ROUTE_TABLE_ID})
    MERGE (subnet)-[r:OCI_ROUTE_TABLE]->(rt)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """
    link_subnet_security_list = """
    MATCH (subnet:OCISubnet{ocid: $SUBNET_ID})
    MATCH (sl:OCISecurityList{ocid: $SECURITY_LIST_ID})
    MERGE (subnet)-[r:OCI_SECURITY_LIST]->(sl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    query = (
        "MATCH (:OCICompartment{ocid: $COMPARTMENT_ID})-[:RESOURCE]->(:OCIVcn)"
        "-[:OCI_SUBNET]->(subnet:OCISubnet) "
        "WHERE subnet.region = $REGION "
        "RETURN subnet.ocid as ocid, subnet.route_table_id as route_table_id, "
        "subnet.security_list_ids as security_list_ids"
    )
    for compartment in compartments:
        subnets = neo4j_session.run(query, COMPARTMENT_ID=compartment["ocid"], REGION=region)
        for subnet in subnets:
            route_table_id = subnet["route_table_id"]
            if route_table_id:
                neo4j_session.run(
                    link_subnet_route_table,
                    SUBNET_ID=subnet["ocid"],
                    ROUTE_TABLE_ID=route_table_id,
                    oci_update_tag=oci_update_tag,
                )
            for security_list_id in (subnet["security_list_ids"] or []):
                neo4j_session.run(
                    link_subnet_security_list,
                    SUBNET_ID=subnet["ocid"],
                    SECURITY_LIST_ID=security_list_id,
                    oci_update_tag=oci_update_tag,
                )


# ============================================================
# VNICs
# ============================================================

def get_vnic_data(
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    vnic_id: str,
) -> Dict[str, Any]:
    """
    Get a single VNIC's details.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Vnic/GetVnic
    """
    try:
        response = network_client.get_vnic(vnic_id)
        return utils.oci_single_object_to_json(response.data)
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve VNIC '%s': %s", vnic_id, e.message,
        )
        return {}


def load_vnics(
    neo4j_session: neo4j.Session,
    vnics: List[Dict[str, Any]],
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI VNIC data into Neo4j, link to subnet, and link to the owning instance
    via its VNIC attachment.
    """
    ingest_vnic = """
    MERGE (vnic:OCIVnic{ocid: $OCID})
    ON CREATE SET vnic.firstseen = timestamp(),
    vnic.createdate = $TIME_CREATED
    SET vnic.display_name = $DISPLAY_NAME,
    vnic.compartment_id = $COMPARTMENT_ID,
    vnic.availability_domain = $AVAILABILITY_DOMAIN,
    vnic.lifecycle_state = $LIFECYCLE_STATE,
    vnic.private_ip = $PRIVATE_IP,
    vnic.public_ip = $PUBLIC_IP,
    vnic.is_primary = $IS_PRIMARY,
    vnic.hostname_label = $HOSTNAME_LABEL,
    vnic.mac_address = $MAC_ADDRESS,
    vnic.skip_source_dest_check = $SKIP_SOURCE_DEST_CHECK,
    vnic.subnet_id = $SUBNET_ID,
    vnic.region = $REGION,
    vnic.lastupdated = $oci_update_tag
    WITH vnic
    OPTIONAL MATCH (subnet:OCISubnet{ocid: $SUBNET_ID})
    FOREACH (_ IN CASE WHEN subnet IS NULL THEN [] ELSE [1] END |
        MERGE (subnet)-[rs:OCI_VNIC]->(vnic)
        ON CREATE SET rs.firstseen = timestamp()
        SET rs.lastupdated = $oci_update_tag
    )
    WITH vnic
    OPTIONAL MATCH (attachment:OCIVnicAttachment{vnic_id: $OCID})
    FOREACH (_ IN CASE WHEN attachment IS NULL THEN [] ELSE [1] END |
        MERGE (attachment)-[ra:OCI_VNIC]->(vnic)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = $oci_update_tag
    )
    """

    for vnic in vnics:
        neo4j_session.run(
            ingest_vnic,
            OCID=vnic.get("id"),
            DISPLAY_NAME=vnic.get("display-name"),
            COMPARTMENT_ID=vnic.get("compartment-id", ""),
            AVAILABILITY_DOMAIN=vnic.get("availability-domain", ""),
            LIFECYCLE_STATE=vnic.get("lifecycle-state"),
            PRIVATE_IP=vnic.get("private-ip", ""),
            PUBLIC_IP=vnic.get("public-ip", ""),
            IS_PRIMARY=vnic.get("is-primary", False),
            HOSTNAME_LABEL=vnic.get("hostname-label", ""),
            MAC_ADDRESS=vnic.get("mac-address", ""),
            SKIP_SOURCE_DEST_CHECK=vnic.get("skip-source-dest-check", False),
            SUBNET_ID=vnic.get("subnet-id", ""),
            REGION=region,
            TIME_CREATED=str(vnic.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_vnics(
    neo4j_session: neo4j.Session,
    network_client: oci.core.virtual_network_client.VirtualNetworkClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync VNICs by reading the VNIC IDs recorded on OCIVnicAttachment nodes (populated by
    compute.sync) and fetching each VNIC's details from the Network API.
    """
    logger.debug("Syncing OCI VNICs for tenancy '%s', region '%s'.", tenancy_id, region)
    query = (
        "MATCH (:OCICompartment{ocid: $COMPARTMENT_ID})-[:RESOURCE]->(inst:OCIInstance)"
        "-[:OCI_VNIC_ATTACHMENT]->(attachment:OCIVnicAttachment) "
        "WHERE attachment.vnic_id IS NOT NULL AND inst.region = $REGION "
        "RETURN DISTINCT attachment.vnic_id as vnic_id"
    )
    for compartment in compartments:
        attachments = neo4j_session.run(query, COMPARTMENT_ID=compartment["ocid"], REGION=region)
        vnics = []
        for attachment in attachments:
            vnic = get_vnic_data(network_client, attachment["vnic_id"])
            if vnic:
                vnics.append(vnic)
        if vnics:
            load_vnics(neo4j_session, vnics, region, oci_update_tag)


# ============================================================
# Flow Logs (from the Logging service)
# ============================================================

def get_log_group_list_data(
    logging_client: "oci.logging.LoggingManagementClient",
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all log groups in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/logging-management/latest/LogGroup/ListLogGroups
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            logging_client.list_log_groups, compartment_id=compartment_id,
        )
        return {'LogGroups': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve log groups for compartment '%s': %s", compartment_id, e.message,
        )
        return {'LogGroups': []}


def get_log_list_data(
    logging_client: "oci.logging.LoggingManagementClient",
    log_group_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all logs within a log group.
    See https://docs.oracle.com/en-us/iaas/api/#/en/logging-management/latest/Log/ListLogs
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            logging_client.list_logs, log_group_id,
        )
        return {'Logs': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve logs for log group '%s': %s", log_group_id, e.message,
        )
        return {'Logs': []}


def load_flow_logs(
    neo4j_session: neo4j.Session,
    logs: List[Dict[str, Any]],
    log_group_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI flow logs (VCN flow logs are service logs sourced from the
    flowlogs/vcn service) into Neo4j and link them to the subnet or VCN they
    are configured for.
    """
    ingest_flow_log = """
    MERGE (fl:OCIFlowLog:OCILog{ocid: $OCID})
    ON CREATE SET fl.firstseen = timestamp(),
    fl.createdate = $TIME_CREATED
    SET fl.display_name = $DISPLAY_NAME,
    fl.compartment_id = $COMPARTMENT_ID,
    fl.log_group_id = $LOG_GROUP_ID,
    fl.log_type = $LOG_TYPE,
    fl.is_enabled = $IS_ENABLED,
    fl.lifecycle_state = $LIFECYCLE_STATE,
    fl.source_service = $SOURCE_SERVICE,
    fl.source_category = $SOURCE_CATEGORY,
    fl.source_resource = $SOURCE_RESOURCE,
    fl.region = $REGION,
    fl.lastupdated = $oci_update_tag
    WITH fl, $SOURCE_RESOURCE as source_resource
    OPTIONAL MATCH (subnet:OCISubnet{ocid: source_resource})
    FOREACH (_ IN CASE WHEN subnet IS NULL THEN [] ELSE [1] END |
        MERGE (subnet)-[rs:OCI_FLOW_LOG]->(fl)
        ON CREATE SET rs.firstseen = timestamp()
        SET rs.lastupdated = $oci_update_tag
    )
    WITH fl, source_resource
    OPTIONAL MATCH (vcn:OCIVcn{ocid: source_resource})
    FOREACH (_ IN CASE WHEN vcn IS NULL THEN [] ELSE [1] END |
        MERGE (vcn)-[rv:OCI_FLOW_LOG]->(fl)
        ON CREATE SET rv.firstseen = timestamp()
        SET rv.lastupdated = $oci_update_tag
    )
    """

    for log in logs:
        configuration = log.get("configuration", {}) or {}
        source = configuration.get("source", {}) or {}
        neo4j_session.run(
            ingest_flow_log,
            OCID=log.get("id"),
            DISPLAY_NAME=log.get("display-name"),
            COMPARTMENT_ID=log.get("compartment-id", ""),
            LOG_GROUP_ID=log.get("log-group-id", log_group_id),
            LOG_TYPE=log.get("log-type", ""),
            IS_ENABLED=log.get("is-enabled", False),
            LIFECYCLE_STATE=log.get("lifecycle-state"),
            SOURCE_SERVICE=source.get("service", ""),
            SOURCE_CATEGORY=source.get("category", ""),
            SOURCE_RESOURCE=source.get("resource", ""),
            REGION=region,
            TIME_CREATED=str(log.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_flow_logs(
    neo4j_session: neo4j.Session,
    logging_client: "oci.logging.LoggingManagementClient",
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync VCN flow logs across compartments. Flow logs are OCI service logs whose
    source service is "flowlogs". We enumerate log groups, then the logs within
    each group, and keep only the flow logs.
    """
    logger.debug("Syncing OCI flow logs for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        log_groups = get_log_group_list_data(logging_client, compartment["ocid"])
        for log_group in log_groups["LogGroups"]:
            log_group_id = log_group.get("id")
            if not log_group_id:
                continue
            data = get_log_list_data(logging_client, log_group_id)
            flow_logs = [
                log for log in data["Logs"]
                if ((log.get("configuration", {}) or {}).get("source", {}) or {}).get("service") == "flowlogs"
            ]
            if flow_logs:
                load_flow_logs(neo4j_session, flow_logs, log_group_id, region, oci_update_tag)


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

    # The Logging service (separate client) provides VCN flow logs. Reuse the
    # network client's config/signer so we authenticate identically.
    logging_client = oci.logging.LoggingManagementClient(
        config=network.base_client.config,
        signer=getattr(network.base_client, "signer", None),
    )

    for region in regions:
        logger.info("Syncing OCI Network in region '%s' for compartment '%s'.", region, compartment_ocid)
        network.base_client.set_region(region)
        logging_client.base_client.set_region(region)

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

        # Link subnets to their route tables and security lists (needs route tables
        # and security lists to already exist).
        sync_subnet_associations(
            neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

        # Sync VNICs (needs OCIVnicAttachment nodes from compute.sync and subnets).
        sync_vnics(
            neo4j_session, network, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

        # Sync VCN flow logs (from the Logging service; links to subnet/VCN).
        sync_flow_logs(
            neo4j_session, logging_client, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

    # Cleanup stale network nodes
    run_cleanup_job('oci_import_network_cleanup.json', neo4j_session, common_job_parameters)
