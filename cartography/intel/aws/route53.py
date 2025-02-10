import logging
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import boto3
import botocore
import neo4j

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def link_aws_resources(neo4j_session: neo4j.Session, update_tag: int) -> None:
    # find records that point to other records
    link_records = """
    MATCH (n:AWSDNSRecord) WITH n MATCH (v:AWSDNSRecord{value: n.name})
    WHERE NOT n = v
    MERGE (v)-[p:DNS_POINTS_TO]->(n)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $update_tag
    """
    neo4j_session.run(link_records, update_tag=update_tag)

    # find records that point to AWS LoadBalancers
    link_elb = """
    MATCH (n:AWSDNSRecord) WITH n MATCH (l:LoadBalancer{dnsname: n.value})
    MERGE (n)-[p:DNS_POINTS_TO]->(l)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $update_tag
    """
    neo4j_session.run(link_elb, update_tag=update_tag)

    # find records that point to AWS LoadBalancersV2
    link_elbv2 = """
    MATCH (n:AWSDNSRecord) WITH n MATCH (l:LoadBalancerV2{dnsname: n.value})
    MERGE (n)-[p:DNS_POINTS_TO]->(l)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $update_tag
    """
    neo4j_session.run(link_elbv2, update_tag=update_tag)

    # find records that point to AWS EC2 Instances
    link_ec2 = """
    MATCH (n:AWSDNSRecord) WITH n MATCH (e:EC2Instance{publicdnsname: n.value})
    MERGE (n)-[p:DNS_POINTS_TO]->(e)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $update_tag
    """
    neo4j_session.run(link_ec2, update_tag=update_tag)


@timeit
def load_a_records(
    neo4j_session: neo4j.Session,
    records: List[Dict],
    update_tag: int,
) -> None:
    ingest_records = """
    UNWIND $records as record
        MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
        ON CREATE SET
            a.firstseen = timestamp(),
            a.name = record.name,
            a.type = record.type
        SET
            a.lastupdated = $update_tag,
            a.value = record.value
        WITH a,record
        MATCH (zone:AWSDNSZone{zoneid: record.zoneid})
        MERGE (a)-[r:MEMBER_OF_DNS_ZONE]->(zone)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_records,
        records=records,
        update_tag=update_tag,
    )


@timeit
def load_alias_records(
    neo4j_session: neo4j.Session,
    records: List[Dict],
    update_tag: int,
) -> None:
    # create the DNSRecord nodes and link them to matching DNSZone and S3Bucket nodes
    ingest_records = """
    UNWIND $records as record
        MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
        ON CREATE SET
            a.firstseen = timestamp(),
            a.name = record.name,
            a.type = record.type
        SET
            a.lastupdated = $update_tag,
            a.value = record.value
        WITH a,record
        MATCH (zone:AWSDNSZone{zoneid: record.zoneid})
        MERGE (a)-[r:MEMBER_OF_DNS_ZONE]->(zone)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_records,
        records=records,
        update_tag=update_tag,
    )


@timeit
def load_cname_records(
    neo4j_session: neo4j.Session,
    records: List[Dict],
    update_tag: int,
) -> None:
    ingest_records = """
    UNWIND $records as record
        MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
        ON CREATE SET
            a.firstseen = timestamp(),
            a.name = record.name,
            a.type = record.type
        SET
            a.lastupdated = $update_tag,
            a.value = record.value
        WITH a,record
        MATCH (zone:AWSDNSZone{zoneid: record.zoneid})
        MERGE (a)-[r:MEMBER_OF_DNS_ZONE]->(zone)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_records,
        records=records,
        update_tag=update_tag,
    )


@timeit
def load_zone(
    neo4j_session: neo4j.Session,
    zone: Dict,
    current_aws_id: str,
    update_tag: int,
) -> None:
    ingest_z = """
    MERGE (zone:DNSZone:AWSDNSZone{zoneid:$ZoneId})
    ON CREATE SET
        zone.firstseen = timestamp(),
        zone.name = $ZoneName
    SET
        zone.lastupdated = $update_tag,
        zone.comment = $Comment,
        zone.privatezone = $PrivateZone
    WITH zone
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(zone)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_z,
        ZoneName=zone["name"][:-1],
        ZoneId=zone["zoneid"],
        Comment=zone["comment"],
        PrivateZone=zone["privatezone"],
        AWS_ACCOUNT_ID=current_aws_id,
        update_tag=update_tag,
    )


@timeit
def load_ns_records(
    neo4j_session: neo4j.Session,
    records: List[Dict],
    zone_name: str,
    update_tag: int,
) -> None:
    ingest_records = """
    UNWIND $records as record
        MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
        ON CREATE SET
            a.firstseen = timestamp(),
            a.name = record.name,
            a.type = record.type
        SET
            a.lastupdated = $update_tag,
            a.value = record.name
        WITH a,record
        MATCH (zone:AWSDNSZone{zoneid: record.zoneid})
        MERGE (a)-[r:MEMBER_OF_DNS_ZONE]->(zone)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH a,record
        UNWIND record.servers as server
            MERGE (ns:NameServer{id:server})
            ON CREATE SET ns.firstseen = timestamp()
            SET
                ns.lastupdated = $update_tag,
                ns.name = server
            MERGE (a)-[pt:DNS_POINTS_TO]->(ns)
            SET pt.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_records,
        records=records,
        update_tag=update_tag,
    )

    # Map the official name servers for a domain.
    map_ns_records = """
    UNWIND $servers as server
        MATCH (ns:NameServer{id:server})
        MATCH (zone:AWSDNSZone{zoneid:$zoneid})
        MERGE (ns)<-[r:NAMESERVER]-(zone)
        SET r.lastupdated = $update_tag
    """
    for record in records:
        if zone_name == record["name"]:
            neo4j_session.run(
                map_ns_records,
                servers=record["servers"],
                zoneid=record["zoneid"],
                update_tag=update_tag,
            )


@timeit
def link_sub_zones(neo4j_session: neo4j.Session, update_tag: int) -> None:
    query = """
    match (z:AWSDNSZone)
    <-[:MEMBER_OF_DNS_ZONE]-
    (record:DNSRecord{type:"NS"})
    -[:DNS_POINTS_TO]->
    (ns:NameServer)
    <-[:NAMESERVER]-
    (z2)
    WHERE record.name=z2.name AND NOT z=z2
    MERGE (z2)<-[r:SUBZONE]-(z)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        query,
        update_tag=update_tag,
    )


@timeit
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


@timeit
def transform_ns_record_set(record_set: Dict, zone_id: str) -> Optional[Dict]:

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
        return None


@timeit
def transform_zone(zone: Dict) -> Dict:
    # TODO simplify this
    if "Comment" in zone["Config"]:
        comment = zone["Config"]["Comment"]
    else:
        comment = ""

    return {
        "zoneid": zone["Id"],
        "name": zone["Name"],
        "privatezone": zone["Config"]["PrivateZone"],
        "comment": comment,
        "count": zone["ResourceRecordSetCount"],
    }


@timeit
def load_dns_details(
    neo4j_session: neo4j.Session,
    dns_details: List[Tuple[Dict, List[Dict]]],
    current_aws_id: str,
    update_tag: int,
) -> None:
    """
    Create the paths
    (:AWSAccount)--(:AWSDNSZone)--(:AWSDNSRecord),
    (:AWSDNSZone)--(:NameServer),
    (:AWSDNSRecord{type:"NS"})-[:DNS_POINTS_TO]->(:NameServer),
    (:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSDNSRecord).
    """
    for zone, zone_record_sets in dns_details:
        zone_a_records = []
        zone_alias_records = []
        zone_cname_records = []
        zone_ns_records = []
        parsed_zone = transform_zone(zone)

        load_zone(neo4j_session, parsed_zone, current_aws_id, update_tag)

        for record_set in zone_record_sets:
            if record_set["Type"] == "A" or record_set["Type"] == "CNAME":
                record = transform_record_set(
                    record_set,
                    zone["Id"],
                    record_set["Name"][:-1],
                )

                if record["type"] == "A":
                    zone_a_records.append(record)
                elif record["type"] == "ALIAS":
                    zone_alias_records.append(record)
                elif record["type"] == "CNAME":
                    zone_cname_records.append(record)

            if record_set["Type"] == "NS":
                record = transform_ns_record_set(record_set, zone["Id"])
                zone_ns_records.append(record)
        if zone_a_records:
            load_a_records(neo4j_session, zone_a_records, update_tag)

        if zone_alias_records:
            load_alias_records(neo4j_session, zone_alias_records, update_tag)

        if zone_cname_records:
            load_cname_records(neo4j_session, zone_cname_records, update_tag)
        if zone_ns_records:
            load_ns_records(
                neo4j_session,
                zone_ns_records,
                parsed_zone["name"][:-1],
                update_tag,
            )
    link_aws_resources(neo4j_session, update_tag)


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
    load_dns_details(neo4j_session, zones, current_aws_account_id, update_tag)
    link_sub_zones(neo4j_session, update_tag)
    cleanup_route53(neo4j_session, current_aws_account_id, update_tag)
