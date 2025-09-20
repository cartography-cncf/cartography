import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.dns import GCPDNSZoneSchema
from cartography.models.gcp.dns import GCPRecordSetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_dns_zones(dns: Resource, project_id: str) -> List[Dict]:
    """Returns a list of DNS zones within the given project."""
    try:
        zones: List[Dict] = []
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
                    "Could not retrieve DNS zones on project %s due to permissions issues. "
                    "Code: %s, Message: %s"
                ),
                project_id,
                err["code"],
                err["message"],
            )
            return []
        raise


@timeit
def get_dns_rrs(dns: Resource, dns_zones: List[Dict], project_id: str) -> List[Dict]:
    """Returns a list of DNS Resource Record Sets within the given project."""
    try:
        rrs: List[Dict] = []
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
                    "Could not retrieve DNS RRS on project %s due to permissions issues. "
                    "Code: %s, Message: %s"
                ),
                project_id,
                err["code"],
                err["message"],
            )
            return []
        raise


@timeit
def transform_dns_zones(dns_zones: List[Dict]) -> List[Dict]:
    """Transform raw DNS zone responses into Neo4j-ready dicts."""
    zones: List[Dict] = []
    for z in dns_zones:
        zones.append(
            {
                "id": z["id"],
                "name": z.get("name"),
                "dns_name": z.get("dnsName"),
                "description": z.get("description"),
                "visibility": z.get("visibility"),
                "kind": z.get("kind"),
                "nameservers": z.get("nameServers"),
                "created_at": z.get("creationTime"),
            }
        )
    return zones


@timeit
def transform_dns_rrs(dns_rrs: List[Dict]) -> List[Dict]:
    """Transform raw DNS record set responses into Neo4j-ready dicts."""
    records: List[Dict] = []
    for r in dns_rrs:
        records.append(
            {
                # Compose a unique ID to avoid collisions across types and zones
                "id": f"{r['name']}|{r.get('type')}|{r.get('zone')}",
                "name": r["name"],
                "type": r.get("type"),
                "ttl": r.get("ttl"),
                "data": r.get("rrdatas"),
                "zone_id": r.get("zone"),
            }
        )
    return records


@timeit
def load_dns_zones(
    neo4j_session: neo4j.Session,
    dns_zones: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """Ingest GCP DNS Zones into Neo4j."""
    load(
        neo4j_session,
        GCPDNSZoneSchema(),
        dns_zones,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_rrs(
    neo4j_session: neo4j.Session,
    dns_rrs: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """Ingest GCP DNS Resource Record Sets into Neo4j."""
    load(
        neo4j_session,
        GCPRecordSetSchema(),
        dns_rrs,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_dns_records(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """Delete out-of-date GCP DNS Zones and Record Sets nodes and relationships."""
    # Record sets depend on zones, so clean them up first.
    GraphJob.from_node_schema(GCPRecordSetSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(GCPDNSZoneSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    dns: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """Get GCP DNS Zones and Record Sets, load them into Neo4j, and clean up old data."""
    logger.info("Syncing DNS records for project %s.", project_id)
    dns_zones_resp = get_dns_zones(dns, project_id)
    dns_zones = transform_dns_zones(dns_zones_resp)
    load_dns_zones(neo4j_session, dns_zones, project_id, gcp_update_tag)
    dns_rrs_resp = get_dns_rrs(dns, dns_zones_resp, project_id)
    dns_rrs = transform_dns_rrs(dns_rrs_resp)
    load_rrs(neo4j_session, dns_rrs, project_id, gcp_update_tag)
    cleanup_dns_records(neo4j_session, common_job_parameters)
