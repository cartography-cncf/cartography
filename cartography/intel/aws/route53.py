import logging
import time
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import boto3
import botocore
import neo4j
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
def get_domains(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    domains = []
    try:
        client = boto3_session.client('route53domains', region_name=region, config=get_botocore_config())
        paginator = client.get_paginator('list_domains')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            domains.extend(page.get('Domains', []))

        return domains

    except ClientError as e:
        logger.error(f'Failed to call Route53Domains list_domains: {region} - {e}')
        return domains


@timeit
def transform_domains(boto3_session: boto3.session.Session, dms: List[Dict], region: str, account_id: str) -> List[Dict]:
    domains = []
    try:
        client = boto3_session.client('route53domains', region_name=region, config=get_botocore_config())
        for domain in dms:
            domain['arn'] = domain['DomainName']
            console_arn = f"arn:aws:route53:{region}:{account_id}:domains/{domain['DomainName']}"
            domain['consolelink'] = aws_console_link.get_console_link(arn=console_arn)
            domain['region'] = region
            domain['details'] = client.get_domain_detail(DomainName=domain['DomainName'])
            domains.append(domain)
    except ClientError as e:
        logger.error(f'Failed to call Route53Domains list_domains: {region} - {e}')

    return domains


def load_domains(session: neo4j.Session, domains: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.execute_write(_load_domains_tx, domains, current_aws_account_id, aws_update_tag)


@timeit
def _load_domains_tx(tx: neo4j.Transaction, domains: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (domain:AWSRoute53Domain{id: record.DomainName})
    ON CREATE SET domain.firstseen = timestamp(),
        domain.arn = record.DomainName
    SET domain.lastupdated = $aws_update_tag,
        domain.name = record.DomainName,
        domain.region = record.region,
        domain.auto_renew = record.AutoRenew,
        domain.transfer_lock = record.TransferLock,
        domain.expiry = record.Expiry,
        domain.consolelink = record.consolelink,
        domain.admin_privacy = record.details.AdminPrivacy,
        domain.registrant_privacy = record.details.RegistrantPrivacy,
        domain.tech_privacy = record.details.TechPrivacy,
        domain.registrar_name = record.details.RegistrarName,
        domain.who_is_server = record.details.WhoIsServer,
        domain.registrar_url = record.details.RegistrarUrl,
        domain.abuse_contact_email = record.details.AbuseContactEmail,
        domain.abuse_contact_phone = record.details.AbuseContactPhone,
        domain.creation_date = record.details.CreationDate,
        domain.expiration_date = record.details.ExpirationDate
    WITH domain
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(domain)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    tx.run(
        query,
        Records=domains,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_domains(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_route53_domains_cleanup.json', neo4j_session, common_job_parameters)


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
def load_a_records(neo4j_session: neo4j.Session, records: List[Dict], update_tag: int) -> None:
    ingest_records = """
    UNWIND $records as record
    MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
    ON CREATE SET a.firstseen = timestamp(), a.name = record.name,
    a.region = record.Region,
    a.arn = record.arn,
    a.type = record.type
    SET a.lastupdated = $update_tag, a.value = record.value
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
def load_alias_records(neo4j_session: neo4j.Session, records: List[Dict], update_tag: int) -> None:
    # create the DNSRecord nodes and link them to matching DNSZone and S3Bucket nodes
    ingest_records = """
    UNWIND $records as record
    MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
    ON CREATE SET a.firstseen = timestamp(), a.name = record.name,
    a.region = record.Region,
    a.arn = record.arn,
    a.type = record.type
    SET a.lastupdated = $update_tag, a.value = record.value
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
def load_cname_records(neo4j_session: neo4j.Session, records: List[Dict], update_tag: int) -> None:
    ingest_records = """
    UNWIND $records as record
    MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
    ON CREATE SET a.firstseen = timestamp(), a.name = record.name,
    a.region = record.Region,
    a.arn = record.arn,
    a.type = record.type
    SET a.lastupdated = $update_tag, a.value = record.value
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
def load_zone(neo4j_session: neo4j.Session, zone: Dict, current_aws_id: str, update_tag: int) -> None:
    ingest_z = """
    MERGE (zone:DNSZone:AWSDNSZone{zoneid: $ZoneId})
    ON CREATE SET zone.firstseen = timestamp(),
    zone.region = $region,
    zone.name = $ZoneName
    SET zone.lastupdated = $update_tag, zone.comment = $Comment, zone.privatezone = $PrivateZone,
    zone.arn = $Arn,
    zone.consolelink = $consolelink
    WITH zone
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(zone)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_z,
        ZoneName=zone['name'][:-1],
        ZoneId=zone['zoneid'],
        consolelink=zone['consolelink'],
        Comment=zone['comment'],
        region="global",
        PrivateZone=zone['privatezone'],
        Arn=zone.get('arn'),
        AWS_ACCOUNT_ID=current_aws_id,
        update_tag=update_tag,
    )


@timeit
def load_ns_records(neo4j_session: neo4j.Session, records: List[Dict], zone_name: str, update_tag: int, consolelink: str) -> None:
    ingest_records = """
    UNWIND $records as record
    MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
    ON CREATE SET a.firstseen = timestamp(), a.name = record.name,
    a.region = record.Region,
    a.consolelink = $consolelink,
    a.type = record.type
    SET a.lastupdated = $update_tag, a.value = record.name
    WITH a,record
    MATCH (zone:AWSDNSZone{zoneid: record.zoneid})
    MERGE (a)-[r:MEMBER_OF_DNS_ZONE]->(zone)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    WITH a,record
    UNWIND record.servers as server
    MERGE (ns:NameServer{id:server})
    ON CREATE SET ns.firstseen = timestamp()
    SET ns.lastupdated = $update_tag, ns.name = server, ns.consolelink = $consolelink
    MERGE (a)-[pt:DNS_POINTS_TO]->(ns)
    SET pt.lastupdated = $update_tag

    """
    neo4j_session.run(
        ingest_records,
        records=records,
        consolelink=consolelink,
        update_tag=update_tag,
    )

    # Map the official name servers for a domain.
    map_ns_records = """
    UNWIND $servers as server
    MATCH (ns:NameServer{id:server})
    MATCH (zone:AWSDNSZone{zoneid: $zoneid})
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
    if record_set['Type'] == 'CNAME':
        if 'AliasTarget' in record_set:
            # this is a weighted CNAME record
            value = record_set['AliasTarget']['DNSName']
            if value.endswith('.'):
                value = value[:-1]
            return {
                "name": name,
                "type": 'CNAME',
                "zoneid": zone_id,
                "value": value,
                "id": _create_dns_record_id(zone_id, name, 'WEIGHTED_CNAME'),
            }
        else:
            # This is a normal CNAME record
            value = record_set['ResourceRecords'][0]['Value']
            if value.endswith('.'):
                value = value[:-1]
            return {
                "name": name,
                "type": 'CNAME',
                "zoneid": zone_id,
                "value": value,
                "id": _create_dns_record_id(zone_id, name, 'CNAME'),
            }

    elif record_set['Type'] == 'A':
        if 'AliasTarget' in record_set:
            # this is an ALIAS record
            # ALIAS records are a special AWS-only type of A record
            return {
                "name": name,
                "type": 'ALIAS',
                "zoneid": zone_id,
                "value": record_set['AliasTarget']['DNSName'][:-1],
                "id": _create_dns_record_id(zone_id, name, 'ALIAS'),
            }
        else:
            # this is a real A record
            # loop and add each value (IP address) to a comma separated string
            # don't forget to trim that trailing comma!
            # TODO can this be replaced with a string join?
            value = ''
            for a_value in record_set['ResourceRecords']:
                value = value + a_value['Value'] + ','

            return {
                "name": name,
                "type": 'A',
                "zoneid": zone_id,
                "value": value[:-1],
                "id": _create_dns_record_id(zone_id, name, 'A'),
            }

    else:
        return None


@timeit
def transform_ns_record_set(record_set: Dict, zone_id: str) -> Optional[Dict]:

    if "ResourceRecords" in record_set:
        # Sometimes the value records have a trailing period, sometimes they dont.
        servers = [_normalize_dns_address(record["Value"]) for record in record_set["ResourceRecords"]]
        return {
            "zoneid": zone_id,
            "type": "NS",
            # looks like "name.some.fqdn.net.", so this removes the trailing comma.
            "name": _normalize_dns_address(record_set["Name"]),
            "servers": servers,
            "id": _create_dns_record_id(zone_id, record_set['Name'][:-1], 'NS'),
        }
    else:
        return None


@timeit
def transform_zone(zone: Dict) -> Dict:
    # TODO simplify this
    if 'Comment' in zone['Config']:
        comment = zone['Config']['Comment']
    else:
        comment = ''

    return {
        "zoneid": zone['Id'],
        "name": zone['Name'],
        "privatezone": zone['Config']['PrivateZone'],
        "comment": comment,
        "count": zone['ResourceRecordSetCount'],
        "arn": zone['arn'],
        "consolelink": zone['consolelink'],
    }


@timeit
def load_dns_details(
    neo4j_session: neo4j.Session, dns_details: List[Tuple[Dict, List[Dict]]], current_aws_id: str,
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
            if record_set['Type'] == 'A' or record_set['Type'] == 'CNAME':
                record = transform_record_set(record_set, zone['Id'], record_set['Name'][:-1])
                record['arn'] = f"arn:aws:route53:::recordset/{record['id']}"

                if record is not None:
                    record["Region"] = record_set.get("Region", "global")

                if record['type'] == 'A':
                    zone_a_records.append(record)
                elif record['type'] == 'ALIAS':
                    zone_alias_records.append(record)
                elif record['type'] == 'CNAME':
                    zone_cname_records.append(record)

            if record_set['Type'] == 'NS':
                record = transform_ns_record_set(record_set, zone['Id'])
                record['arn'] = f"arn:aws:route53:::recordset/{record['id']}"
                if record is not None:
                    record["Region"] = record_set.get("Region", "global")

                zone_ns_records.append(record)

        if zone_a_records:
            load_a_records(neo4j_session, zone_a_records, update_tag)

        if zone_alias_records:
            load_alias_records(neo4j_session, zone_alias_records, update_tag)

        if zone_cname_records:
            load_cname_records(neo4j_session, zone_cname_records, update_tag)

        if zone_ns_records:
            load_ns_records(neo4j_session, zone_ns_records, parsed_zone['name'][:-1], update_tag, zone['consolelink'])

    link_aws_resources(neo4j_session, update_tag)


@timeit
def get_zone_record_sets(client: botocore.client.BaseClient, zone_id: str) -> List[Dict]:
    resource_record_sets: List[Dict] = []
    paginator = client.get_paginator('list_resource_record_sets')
    pages = paginator.paginate(HostedZoneId=zone_id)
    for page in pages:
        resource_record_sets.extend(page['ResourceRecordSets'])
    return resource_record_sets


@timeit
def get_zones(client: botocore.client.BaseClient) -> List[Dict]:
    paginator = client.get_paginator('list_hosted_zones')
    hosted_zones: List[Dict] = []
    for page in paginator.paginate():
        hosted_zones.extend(page['HostedZones'])
    return hosted_zones


@timeit
def transform_zones(client: botocore, zns: List[Dict]) -> List[Tuple[Dict, List[Dict]]]:
    results: List[Tuple[Dict, List[Dict]]] = []
    for hosted_zone in zns:
        hosted_zone['arn'] = f"arn:aws:route53:::hostedzone/{hosted_zone['Id']}"
        hosted_zone['consolelink'] = aws_console_link.get_console_link(arn=hosted_zone['arn'])
        record_sets = get_zone_record_sets(client, hosted_zone['Id'])
        results.append((hosted_zone, record_sets))
    return results


def _create_dns_record_id(zoneid: str, name: str, record_type: str) -> str:
    return "/".join([zoneid, name, record_type])


def _normalize_dns_address(address: str) -> str:
    return address.rstrip('.')


@timeit
def cleanup_route53(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_dns_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Route53 for account '%s', at %s.", current_aws_account_id, tic)
    client = boto3_session.client('route53')
    zns = get_zones(client)
    zones = transform_zones(client, zns)

    logger.info(f"Total Route53 Zones: {len(zones)}")

    load_dns_details(neo4j_session, zones, current_aws_account_id, update_tag)
    link_sub_zones(neo4j_session, update_tag)
    cleanup_route53(neo4j_session, common_job_parameters)

    # Route53 has only 1 region. us-east-1
    # https://github.com/aws/aws-cli/issues/1354
    regions = ['us-east-1']

    domains = []
    for region in regions:
        logger.info("Syncing Route53 Domains for region '%s' in account '%s'.", region, current_aws_account_id)

        dms = get_domains(boto3_session, region)
        domains.extend(transform_domains(boto3_session, dms, region, current_aws_account_id))

    logger.info(f"Total Route Domains: {len(domains)}")

    load_domains(neo4j_session, domains, current_aws_account_id, update_tag)

    cleanup_domains(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Route53: {toc - tic:0.4f} seconds")
