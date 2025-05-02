import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_dns_zones(dns: Resource, project_id: str) -> List[Resource]:
    """
    Returns a list of DNS zones within the given project.

    :type dns: The GCP DNS resource object
    :param dns: The DNS resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: Current Google Project Id

    :rtype: list
    :return: List of DNS zones
    """
    try:
        zones = []
        request = dns.managedZones().list(project=project_id)
        while request is not None:
            response = request.execute()
            for managed_zone in response["managedZones"]:
                zones.append(managed_zone)
            request = dns.managedZones().list_next(
                previous_request=request,
                previous_response=response,
            )
        return zones
    except HttpError as e:
        err = json.loads(e.content.decode("utf-8"))["error"]
        if (
            err.get("status", "") == "PERMISSION_DENIED"
            or err.get("message", "") == "Forbidden"
        ):
            logger.warning(
                (
                    "Could not retrieve DNS zones on project %s due to permissions issues. Code: %s, Message: %s"
                ),
                project_id,
                err["code"],
                err["message"],
            )
            return []
        else:
            raise


@timeit
def get_dns_rrs(
    dns: Resource,
    dns_zones: List[Dict],
    project_id: str,
) -> List[Resource]:
    """
    Returns a list of DNS Resource Record Sets within the given project.

    :type dns: The GCP DNS resource object
    :param dns: The DNS resource object created by googleapiclient.discovery.build()

    :type dns_zones: list
    :param dns_zones: List of DNS zones for the project

    :type project_id: str
    :param project_id: Current Google Project Id

    :rtype: list
    :return: List of Resource Record Sets
    """
    try:
        rrs: List[Resource] = []
        for zone in dns_zones:
            request = dns.resourceRecordSets().list(
                project=project_id,
                managedZone=zone["id"],
            )
            while request is not None:
                response = request.execute()
                for resource_record_set in response["rrsets"]:
                    resource_record_set["zone"] = zone["id"]
                    rrs.append(resource_record_set)
                request = dns.resourceRecordSets().list_next(
                    previous_request=request,
                    previous_response=response,
                )
        return rrs
    except HttpError as e:
        err = json.loads(e.content.decode("utf-8"))["error"]
        if (
            err.get("status", "") == "PERMISSION_DENIED"
            or err.get("message", "") == "Forbidden"
        ):
            logger.warning(
                (
                    "Could not retrieve DNS RRS on project %s due to permissions issues. Code: %s, Message: %s"
                ),
                project_id,
                err["code"],
                err["message"],
            )
            return []
        else:
            raise
        raise e


@timeit
def load_dns_zones(
    neo4j_session: neo4j.Session,
    dns_zones: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP DNS Zones into Neo4j

    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type dns_resp: Dict
    :param dns_resp: A DNS response object from the GKE API

    :type project_id: str
    :param project_id: Current Google Project Id

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    """

    ingest_records = """
    UNWIND $records as record
    MERGE(zone:GCPDNSZone{id:record.id})
    ON CREATE SET
        zone.firstseen = timestamp(),
        zone.created_at = record.creationTime
    SET
        zone.name = record.name,
        zone.dns_name = record.dnsName,
        zone.description = record.description,
        zone.visibility = record.visibility,
        zone.kind = record.kind,
        zone.nameservers = record.nameServers,
        zone.lastupdated = $gcp_update_tag
    WITH zone
    MATCH (owner:GCPProject{id:$ProjectId})
    MERGE (owner)-[r:RESOURCE]->(zone)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        ingest_records,
        records=dns_zones,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_rrs(
    neo4j_session: neo4j.Session,
    dns_rrs: List[Resource],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP RRS into Neo4j

    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type dns_rrs: list
    :param dns_rrs: A list of RRS

    :type project_id: str
    :param project_id: Current Google Project Id

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    """

    ingest_records = """
    UNWIND $records as record
    MERGE(rrs:GCPRecordSet{id:record.name})
    ON CREATE SET
        rrs.firstseen = timestamp()
    SET
        rrs.name = record.name,
        rrs.type = record.type,
        rrs.ttl = record.ttl,
        rrs.data = record.rrdatas,
        rrs.lastupdated = $gcp_update_tag
    WITH rrs, record
    MATCH (zone:GCPDNSZone{id:record.zone})
    MERGE (zone)-[r:HAS_RECORD]->(rrs)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        ingest_records,
        records=dns_rrs,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_dns_records(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Delete out-of-date GCP DNS Zones and RRS nodes and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job("gcp_dns_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    dns: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP DNS Zones and Resource Record Sets using the DNS resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type dns: The DNS resource object created by googleapiclient.discovery.build()
    :param dns: The GCP DNS resource object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    logger.info("Syncing DNS records for project %s.", project_id)
    # DNS ZONES
    dns_zones = get_dns_zones(dns, project_id)
    load_dns_zones(neo4j_session, dns_zones, project_id, gcp_update_tag)
    # RECORD SETS
    dns_rrs = get_dns_rrs(dns, dns_zones, project_id)
    load_rrs(neo4j_session, dns_rrs, project_id, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/cartography-cncf/cartography/issues/381
    cleanup_dns_records(neo4j_session, common_job_parameters)
