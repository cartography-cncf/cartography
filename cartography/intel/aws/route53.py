import logging
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

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
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

DnsData = namedtuple(
    "DnsData",
    [
        "a_records",
        "alias_records",
        "cname_records",
        "ns_records",
        "name_servers",
    ],
)

TransformedDnsData = namedtuple(
    "TransformedDnsData",
    [
        "zones",
        "a_records",
        "alias_records",
        "cname_records",
        "ns_records",
        "name_servers",
    ],
)


@timeit
def load_a_records(
    neo4j_session: neo4j.Session,
    records: List[Dict],
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
    records: List[Dict],
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
    records: List[Dict],
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
def load_zone(
    neo4j_session: neo4j.Session,
    zone: Dict,
    current_aws_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSDNSZoneSchema(),
        [zone],
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
    Create SUBZONE relationships between DNS zones using MatchLinks.

    This function finds relationships where:
    1. A DNS zone has an NS record that points to a nameserver
    2. That nameserver is associated with another DNS zone
    3. The NS record's name matches the other zone's name
    4. This creates a parent-child relationship between zones
    """
    query = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(z:AWSDNSZone)<-[:MEMBER_OF_DNS_ZONE]-(record:DNSRecord{type:"NS"})-[:DNS_POINTS_TO]->(ns:NameServer)<-[:NAMESERVER]-(z2:AWSDNSZone)
    WHERE record.name=z2.name AND NOT z=z2
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


def transform_record_set(record_set: Dict, zone_id: str, name: str) -> Optional[Dict]:
    # process CNAME, ALIAS and A records
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
            # don't forget to trim that trailing comma!
            # TODO can this be replaced with a string join?
            value = ""
            for a_value in record_set["ResourceRecords"]:
                value = value + a_value["Value"] + ","

            return {
                "name": name,
                "type": "A",
                "zoneid": zone_id,
                "value": value[:-1],
                "id": _create_dns_record_id(zone_id, name, "A"),
            }

    else:
        return None


def transform_ns_record_set(record_set: Dict, zone_id: str) -> dict[str, Any] | None:
    if "ResourceRecords" in record_set:
        # Sometimes the value records have a trailing period, sometimes they dont.
        servers = [
            _normalize_dns_address(record["Value"])
            for record in record_set["ResourceRecords"]
        ]
        #        import pdb; pdb.set_trace()
        return {
            "zoneid": zone_id,
            "type": "NS",
            # looks like "name.some.fqdn.net.", so this removes the trailing comma.
            "name": _normalize_dns_address(record_set["Name"]),
            "servers": servers,
            "id": _create_dns_record_id(zone_id, record_set["Name"][:-1], "NS"),
        }
    else:
        return None


def transform_zone(zone: Dict) -> Dict:
    # TODO simplify this
    if "Comment" in zone["Config"]:
        comment = zone["Config"]["Comment"]
    else:
        comment = ""

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


def transform_dns_records(
    zone_record_sets: List[Dict],
    zone_id: str,
) -> DnsData:
    a_records = []
    alias_records = []
    cname_records = []
    ns_records = []

    name_servers: list[dict[str, Any]] = []

    for record_set in zone_record_sets:
        if record_set["Type"] == "A" or record_set["Type"] == "CNAME":
            record = transform_record_set(
                record_set,
                zone_id,
                record_set["Name"][:-1],
            )

            if record and record["type"] == "A":
                a_records.append(record)
            elif record and record["type"] == "ALIAS":
                alias_records.append(record)
            elif record and record["type"] == "CNAME":
                cname_records.append(record)

        if record_set["Type"] == "NS":
            record = transform_ns_record_set(record_set, zone_id)
            if record:
                ns_records.append(record)
                name_servers.extend(
                    [{"id": server, "zoneid": zone_id} for server in record["servers"]]
                )

    return DnsData(
        a_records=a_records,
        alias_records=alias_records,
        cname_records=cname_records,
        ns_records=ns_records,
        name_servers=name_servers,
    )


def transform_all_dns_data(
    zones: List[Tuple[Dict, List[Dict]]],
) -> TransformedDnsData:
    """
    Transform all DNS data into flat lists for loading.
    Returns: (zones, a_records, alias_records, cname_records, ns_records)
    """
    transformed_zones = []
    all_a_records = []
    all_alias_records = []
    all_cname_records = []
    all_ns_records = []
    all_name_servers = []

    for zone, zone_record_sets in zones:
        # Transform zone
        parsed_zone = transform_zone(zone)
        transformed_zones.append(parsed_zone)

        # TODO try to unnest this
        # Transform records
        dns_data: DnsData = transform_dns_records(zone_record_sets, zone["Id"])

        # Add zone name to NS records for loading
        zone_name = parsed_zone["name"]
        for ns_record in dns_data.ns_records:
            ns_record["zone_name"] = zone_name

        all_a_records.extend(dns_data.a_records)
        all_alias_records.extend(dns_data.alias_records)
        all_cname_records.extend(dns_data.cname_records)
        all_ns_records.extend(dns_data.ns_records)
        all_name_servers.extend(dns_data.name_servers)

    return TransformedDnsData(
        zones=transformed_zones,
        a_records=all_a_records,
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
    alias_records: list[dict[str, Any]],
    cname_records: list[dict[str, Any]],
    ns_records: list[dict[str, Any]],
    name_servers: list[str],
    current_aws_id: str,
    update_tag: int,
) -> None:
    # Load zones
    for zone in zones:
        load_zone(neo4j_session, zone, current_aws_id, update_tag)

    # Load records
    load_a_records(neo4j_session, a_records, update_tag, current_aws_id)
    load_alias_records(neo4j_session, alias_records, update_tag, current_aws_id)
    load_cname_records(neo4j_session, cname_records, update_tag, current_aws_id)
    load_name_servers(neo4j_session, name_servers, update_tag, current_aws_id)
    load_ns_records(neo4j_session, ns_records, update_tag, current_aws_id)


@timeit
def load_dns_details(
    neo4j_session: neo4j.Session,
    dns_details: List[Tuple[Dict, List[Dict]]],
    current_aws_id: str,
    update_tag: int,
) -> None:
    """
    Backward-compatible wrapper for the flat loader. Accepts the old signature.
    """
    transformed_data = transform_all_dns_data(dns_details)
    _load_dns_details_flat(
        neo4j_session,
        transformed_data.zones,
        transformed_data.a_records,
        transformed_data.alias_records,
        transformed_data.cname_records,
        transformed_data.ns_records,
        transformed_data.name_servers,
        current_aws_id,
        update_tag,
    )


@timeit
def get_zone_record_sets(
    client: botocore.client.BaseClient,
    zone_id: str,
) -> List[Dict]:
    resource_record_sets: List[Dict] = []
    paginator = client.get_paginator("list_resource_record_sets")
    pages = paginator.paginate(HostedZoneId=zone_id)
    for page in pages:
        resource_record_sets.extend(page["ResourceRecordSets"])
    return resource_record_sets


@timeit
def get_zones(client: botocore.client.BaseClient) -> List[Tuple[Dict, List[Dict]]]:
    paginator = client.get_paginator("list_hosted_zones")
    hosted_zones: List[Dict] = []
    for page in paginator.paginate():
        hosted_zones.extend(page["HostedZones"])

    results: List[Tuple[Dict, List[Dict]]] = []
    for hosted_zone in hosted_zones:
        record_sets = get_zone_record_sets(client, hosted_zone["Id"])
        results.append((hosted_zone, record_sets))
    return results


def _create_dns_record_id(zoneid: str, name: str, record_type: str) -> str:
    return "/".join([zoneid, name, record_type])


def _normalize_dns_address(address: str) -> str:
    return address.rstrip(".")


@timeit
def cleanup_route53(
    neo4j_session: neo4j.Session,
    current_aws_id: str,
    update_tag: int,
) -> None:
    run_cleanup_job(
        "aws_dns_cleanup.json",
        neo4j_session,
        {"UPDATE_TAG": update_tag, "AWS_ID": current_aws_id},
    )
    # Clean up stale relationships
    cleanup_job = GraphJob.from_matchlink(
        AWSDNSZoneSubzoneMatchLink(),
        "AWSAccount",
        current_aws_id,
        update_tag,
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Route53 for account '%s'.", current_aws_account_id)
    client = boto3_session.client("route53")
    zones = get_zones(client)

    # Transform the data
    transformed_data = transform_all_dns_data(zones)

    _load_dns_details_flat(
        neo4j_session,
        transformed_data.zones,
        transformed_data.a_records,
        transformed_data.alias_records,
        transformed_data.cname_records,
        transformed_data.ns_records,
        transformed_data.name_servers,
        current_aws_account_id,
        update_tag,
    )
    link_sub_zones(neo4j_session, update_tag, current_aws_account_id)
    cleanup_route53(neo4j_session, current_aws_account_id, update_tag)
