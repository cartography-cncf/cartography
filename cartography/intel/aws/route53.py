import logging
from collections import namedtuple
from typing import Any

import boto3
import botocore
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.aws.route53.dnsrecord import AWSDNSRecordSchema
from cartography.models.aws.route53.nameserver import NameServerSchema
from cartography.models.aws.route53.subzone import AWSDNSZoneSubzoneMatchLink
from cartography.models.aws.route53.zone import AWSDNSZoneSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

DnsData = namedtuple(
    "DnsData",
    [
        "zones",
        "a_records",
        "aaaa_records",
        "alias_records",
        "cname_records",
        "ns_records",
        "name_servers",
    ],
)


def _create_dns_record_id(zoneid: str, name: str, record_type: str) -> str:
    return "/".join([zoneid, name, record_type])


def _normalize_dns_address(address: str) -> str:
    return address.rstrip(".")


@timeit
def get_zone_record_sets(
    client: botocore.client.BaseClient,
    zone_id: str,
) -> list[dict[str, Any]]:
    resource_record_sets: list[dict[str, Any]] = []
    paginator = client.get_paginator("list_resource_record_sets")
    pages = paginator.paginate(HostedZoneId=zone_id)
    for page in pages:
        resource_record_sets.extend(page["ResourceRecordSets"])
    return resource_record_sets


@aws_handle_regions
@timeit
def get_zones(
    client: botocore.client.BaseClient,
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    paginator = client.get_paginator("list_hosted_zones")
    hosted_zones: list[dict[str, Any]] = []
    for page in paginator.paginate():
        hosted_zones.extend(page["HostedZones"])

    results: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for hosted_zone in hosted_zones:
        record_sets = get_zone_record_sets(client, hosted_zone["Id"])
        results.append((hosted_zone, record_sets))
    return results


def transform_record_set(
    record_set: dict[str, Any], zone_id: str, name: str
) -> dict[str, Any] | None:
    # process CNAME, ALIAS, A, and AAAA records
    if record_set["Type"] == "CNAME":
        if "AliasTarget" in record_set:
            # this is a weighted CNAME record
            value = record_set["AliasTarget"]["DNSName"]
            if value.endswith("."):
                value = value[:-1]
            return {
                "name": name,
                "type": "CNAME",
                "zoneid": zone_id,
                "value": value,
                "id": _create_dns_record_id(zone_id, name, "WEIGHTED_CNAME"),
            }
        else:
            # This is a normal CNAME record
            value = record_set["ResourceRecords"][0]["Value"]
            if value.endswith("."):
                value = value[:-1]
            return {
                "name": name,
                "type": "CNAME",
                "zoneid": zone_id,
                "value": value,
                "id": _create_dns_record_id(zone_id, name, "CNAME"),
            }

    elif record_set["Type"] == "A":
        if "AliasTarget" in record_set:
            # this is an ALIAS record
            # ALIAS records are a special AWS-only type of A record
            return {
                "name": name,
                "type": "ALIAS",
                "zoneid": zone_id,
                "value": record_set["AliasTarget"]["DNSName"][:-1],
                "id": _create_dns_record_id(zone_id, name, "ALIAS"),
            }
        else:
            # this is a real A record
            # loop and add each value (IP address) to a comma separated string
            # TODO if there are many IPs, this string will be long. we should change this.
            ip_addresses = [record["Value"] for record in record_set["ResourceRecords"]]
            value = ",".join(ip_addresses)

            return {
                "name": name,
                "type": "A",
                "zoneid": zone_id,
                # Include the IPs for relationships
                "ip_addresses": ip_addresses,
                "value": value,
                "id": _create_dns_record_id(zone_id, name, "A"),
            }
    elif record_set["Type"] == "AAAA":
        if "AliasTarget" in record_set:
            # AAAA alias records follow the same pattern as A aliases but map to IPv6 targets
            value = record_set["AliasTarget"]["DNSName"]
            if value.endswith("."):
                value = value[:-1]
            return {
                "name": name,
                "type": "ALIAS",
                "zoneid": zone_id,
                "value": value,
                "id": _create_dns_record_id(zone_id, name, "ALIAS_AAAA"),
            }
        else:
            ip_addresses = [record["Value"] for record in record_set["ResourceRecords"]]
            value = ",".join(ip_addresses)

            return {
                "name": name,
                "type": "AAAA",
                "zoneid": zone_id,
                "ip_addresses": ip_addresses,
                "value": value,
                "id": _create_dns_record_id(zone_id, name, "AAAA"),
            }
    # This should never happen since we only call this for A and CNAME records,
    # but we'll log it and return None.
    logger.warning(f"Unsupported record type: {record_set['Type']}")
    return None


def transform_ns_record_set(
    record_set: dict[str, Any], zone_id: str
) -> dict[str, Any] | None:
    if "ResourceRecords" in record_set:
        # Sometimes the value records have a trailing period, sometimes they dont.
        servers = [
            _normalize_dns_address(record["Value"])
            for record in record_set["ResourceRecords"]
        ]
        return {
            "zoneid": zone_id,
            "type": "NS",
            # looks like "name.some.fqdn.net.", so this removes the trailing comma.
            "name": _normalize_dns_address(record_set["Name"]),
            "servers": servers,
            "id": _create_dns_record_id(zone_id, record_set["Name"][:-1], "NS"),
        }
    else:
        # This should never happen since we only call this for NS records
        # but we'll log it and return None.
        logger.warning(f"NS record set missing ResourceRecords: {record_set}")
        return None


def transform_zone(zone: dict[str, Any]) -> dict[str, Any]:
    comment = zone["Config"].get("Comment")

    # Remove trailing dot from name for schema compatibility
    zone_name = zone["Name"]
    if zone_name.endswith("."):
        zone_name = zone_name[:-1]

    return {
        "zoneid": zone["Id"],
        "name": zone_name,
        "privatezone": zone["Config"]["PrivateZone"],
        "comment": comment,
        "count": zone["ResourceRecordSetCount"],
    }


def transform_all_dns_data(
    zones: list[tuple[dict[str, Any], list[dict[str, Any]]]],
) -> DnsData:
    """
    Transform all DNS data into flat lists for loading.
    Returns: (zones, a_records, aaaa_records, alias_records, cname_records, ns_records)
    """
    transformed_zones = []
    all_a_records = []
    all_aaaa_records = []
    all_alias_records = []
    all_cname_records = []
    all_ns_records = []
    all_name_servers = []

    for zone, zone_record_sets in zones:
        parsed_zone = transform_zone(zone)
        transformed_zones.append(parsed_zone)

        zone_id = zone["Id"]
        zone_name = parsed_zone["name"]

        for rs in zone_record_sets:
            if rs["Type"] in {"A", "AAAA", "CNAME"}:
                transformed_rs = transform_record_set(
                    rs,
                    zone_id,
                    rs["Name"][:-1],
                )
                if transformed_rs is None:
                    continue

                if transformed_rs["type"] == "A":
                    all_a_records.append(transformed_rs)
                    # TODO consider creating IPs as a first-class node from here.
                    # Right now we just match on them from the A record.
                elif transformed_rs["type"] == "AAAA":
                    all_aaaa_records.append(transformed_rs)
                elif transformed_rs["type"] == "ALIAS":
                    all_alias_records.append(transformed_rs)
                elif transformed_rs["type"] == "CNAME":
                    all_cname_records.append(transformed_rs)

            elif rs["Type"] == "NS":
                transformed_rs = transform_ns_record_set(rs, zone_id)
                if transformed_rs is None:
                    continue

                # Add zone name to NS records for loading
                transformed_rs["zone_name"] = zone_name
                all_ns_records.append(transformed_rs)
                all_name_servers.extend(
                    [
                        {"id": server, "zoneid": zone_id}
                        for server in transformed_rs["servers"]
                    ]
                )

    return DnsData(
        zones=transformed_zones,
        a_records=all_a_records,
        aaaa_records=all_aaaa_records,
        alias_records=all_alias_records,
        cname_records=all_cname_records,
        ns_records=all_ns_records,
        name_servers=all_name_servers,
    )


@timeit
def _load_dns_details_flat(
    neo4j_session: neo4j.Session,
    zones: list[dict[str, Any]],
    a_records: list[dict[str, Any]],
    aaaa_records: list[dict[str, Any]],
    alias_records: list[dict[str, Any]],
    cname_records: list[dict[str, Any]],
    ns_records: list[dict[str, Any]],
    name_servers: list[dict[str, Any]],
    current_aws_id: str,
    update_tag: int,
) -> None:
    load_zones(neo4j_session, zones, current_aws_id, update_tag)
    load_a_records(neo4j_session, a_records, update_tag, current_aws_id)
    load_aaaa_records(neo4j_session, aaaa_records, update_tag, current_aws_id)
    load_alias_records(neo4j_session, alias_records, update_tag, current_aws_id)
    load_cname_records(neo4j_session, cname_records, update_tag, current_aws_id)
    load_name_servers(neo4j_session, name_servers, update_tag, current_aws_id)
    load_ns_records(neo4j_session, ns_records, update_tag, current_aws_id)


@timeit
def load_dns_details(
    neo4j_session: neo4j.Session,
    dns_details: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    current_aws_id: str,
    update_tag: int,
) -> None:
    """
    Backward-compatible wrapper
    """
    transformed_data = transform_all_dns_data(dns_details)
    _load_dns_details_flat(
        neo4j_session,
        transformed_data.zones,
        transformed_data.a_records,
        transformed_data.aaaa_records,
        transformed_data.alias_records,
        transformed_data.cname_records,
        transformed_data.ns_records,
        transformed_data.name_servers,
        current_aws_id,
        update_tag,
    )


@timeit
def load_a_records(
    neo4j_session: neo4j.Session,
    records: list[dict[str, Any]],
    update_tag: int,
    current_aws_id: str,
) -> None:
    load(
        neo4j_session,
        AWSDNSRecordSchema(),
        records,
        lastupdated=update_tag,
        AWS_ID=current_aws_id,
    )


@timeit
def load_aaaa_records(
    neo4j_session: neo4j.Session,
    records: list[dict[str, Any]],
    update_tag: int,
    current_aws_id: str,
) -> None:
    load(
        neo4j_session,
        AWSDNSRecordSchema(),
        records,
        lastupdated=update_tag,
        AWS_ID=current_aws_id,
    )


@timeit
def load_alias_records(
    neo4j_session: neo4j.Session,
    records: list[dict[str, Any]],
    update_tag: int,
    current_aws_id: str,
) -> None:
    load(
        neo4j_session,
        AWSDNSRecordSchema(),
        records,
        lastupdated=update_tag,
        AWS_ID=current_aws_id,
    )


@timeit
def load_cname_records(
    neo4j_session: neo4j.Session,
    records: list[dict[str, Any]],
    update_tag: int,
    current_aws_id: str,
) -> None:
    load(
        neo4j_session,
        AWSDNSRecordSchema(),
        records,
        lastupdated=update_tag,
        AWS_ID=current_aws_id,
    )


@timeit
def load_zones(
    neo4j_session: neo4j.Session,
    zones: list[dict[str, Any]],
    current_aws_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSDNSZoneSchema(),
        zones,
        lastupdated=update_tag,
        AWS_ID=current_aws_id,
    )


@timeit
def load_ns_records(
    neo4j_session: neo4j.Session,
    records: list[dict[str, Any]],
    update_tag: int,
    current_aws_id: str,
) -> None:
    load(
        neo4j_session,
        AWSDNSRecordSchema(),
        records,
        lastupdated=update_tag,
        AWS_ID=current_aws_id,
    )


@timeit
def load_name_servers(
    neo4j_session: neo4j.Session,
    name_servers: list[dict[str, Any]],
    update_tag: int,
    current_aws_id: str,
) -> None:
    load(
        neo4j_session,
        NameServerSchema(),
        name_servers,
        lastupdated=update_tag,
        AWS_ID=current_aws_id,
    )


@timeit
def link_sub_zones(
    neo4j_session: neo4j.Session, update_tag: int, current_aws_id: str
) -> None:
    """
    Create SUBZONE relationships between DNS zones using matchlinks.

    A DNS zone B is a sub zone of A if:
    1. DNS zone A has an NS record that points to a nameserver
    2. That nameserver is associated with DNS zone B
    3. The NS record's name matches the name of DNS zone B

    We use matchlinks instead of a regular relationship because the hierarchy
    isn't known ahead of time.
    """
    query = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(z:AWSDNSZone)
        <-[:MEMBER_OF_DNS_ZONE]-(record:DNSRecord{type:"NS"})
        -[:DNS_POINTS_TO]->(ns:NameServer)<-[:NAMESERVER]-(z2:AWSDNSZone)
        WHERE record.name = z2.name AND
        z2.name ENDS WITH '.' + z.name AND
        NOT z = z2
    RETURN z.id as zone_id, z2.id as subzone_id
    """
    zone_to_subzone = neo4j_session.read_transaction(
        read_list_of_dicts_tx, query, AWS_ID=current_aws_id
    )
    load_matchlinks(
        neo4j_session,
        AWSDNSZoneSubzoneMatchLink(),
        zone_to_subzone,
        lastupdated=update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_id,
    )


@timeit
def cleanup_route53(
    neo4j_session: neo4j.Session,
    current_aws_id: str,
    update_tag: int,
) -> None:
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "AWS_ID": current_aws_id,
    }
    GraphJob.from_node_schema(
        AWSDNSRecordSchema(),
        common_job_parameters,
    ).run(neo4j_session)

    GraphJob.from_node_schema(
        NameServerSchema(),
        common_job_parameters,
    ).run(neo4j_session)

    GraphJob.from_node_schema(
        AWSDNSZoneSchema(),
        common_job_parameters,
    ).run(neo4j_session)

    GraphJob.from_matchlink(
        AWSDNSZoneSubzoneMatchLink(),
        "AWSAccount",
        current_aws_id,
        update_tag,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing Route53 for account '%s'.", current_aws_account_id)
    client = boto3_session.client("route53")
    zones = get_zones(client)

    transformed_data = transform_all_dns_data(zones)

    _load_dns_details_flat(
        neo4j_session,
        transformed_data.zones,
        transformed_data.a_records,
        transformed_data.aaaa_records,
        transformed_data.alias_records,
        transformed_data.cname_records,
        transformed_data.ns_records,
        transformed_data.name_servers,
        current_aws_account_id,
        update_tag,
    )
    link_sub_zones(neo4j_session, update_tag, current_aws_account_id)
    cleanup_route53(neo4j_session, current_aws_account_id, update_tag)
