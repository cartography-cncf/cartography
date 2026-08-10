import logging
from typing import Any

import neo4j
import scaleway
from scaleway.domain.v2beta1 import DNSZone
from scaleway.domain.v2beta1 import DomainV2Beta1API
from scaleway.domain.v2beta1 import Record

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.dns.dnsrecord import ScalewayDnsRecordSchema
from cartography.models.scaleway.dns.dnszone import ScalewayDnsZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _zone_full_name(zone: DNSZone) -> str:
    """Return the {subdomain}.{domain} string the Scaleway API uses as zone path param.

    When ``subdomain`` is empty the zone is the apex of the domain itself.
    """
    if zone.subdomain:
        return f"{zone.subdomain}.{zone.domain}"
    return zone.domain


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    zones, records_by_zone = get(client, org_id)
    zones_by_project, records_by_project = transform_dns(zones, records_by_zone)
    load_dns(neo4j_session, zones_by_project, records_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[DNSZone], dict[str, list[Record]]]:
    api = DomainV2Beta1API(client)
    # `domain=""` lists every DNS zone visible to the org (the filter is empty).
    zones = api.list_dns_zones_all(domain="", organization_id=org_id)
    records_by_zone: dict[str, list[Record]] = {}
    for zone in zones:
        zone_name = _zone_full_name(zone)
        # `name=""` lists every record in the zone. We pass `project_id`
        # explicitly: the SDK falls back to the client's default project
        # when omitted, which would silently drop records from zones owned
        # by other projects.
        records_by_zone[zone_name] = api.list_dns_zone_records_all(
            dns_zone=zone_name, name="", project_id=zone.project_id
        )
    return zones, records_by_zone


def transform_dns(
    zones: list[DNSZone],
    records_by_zone: dict[str, list[Record]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    zones_by_project: dict[str, list[dict[str, Any]]] = {}
    records_by_project: dict[str, list[dict[str, Any]]] = {}
    for zone in zones:
        zone_name = _zone_full_name(zone)
        formatted_zone = scaleway_obj_to_dict(zone)
        formatted_zone["id"] = zone_name
        zones_by_project.setdefault(zone.project_id, []).append(formatted_zone)
        for record in records_by_zone.get(zone_name, []):
            formatted_record = scaleway_obj_to_dict(record)
            formatted_record["zone_id"] = zone_name
            records_by_project.setdefault(zone.project_id, []).append(formatted_record)
    return zones_by_project, records_by_project


@timeit
def load_dns(
    neo4j_session: neo4j.Session,
    zones_by_project: dict[str, list[dict[str, Any]]],
    records_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, zones in zones_by_project.items():
        logger.info(
            "Loading %d Scaleway DNS zones in project '%s' into Neo4j.",
            len(zones),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayDnsZoneSchema(),
            zones,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, records in records_by_project.items():
        load(
            neo4j_session,
            ScalewayDnsRecordSchema(),
            records,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        # Records before zones (records depend on zones).
        GraphJob.from_node_schema(ScalewayDnsRecordSchema(), scoped_job_parameters).run(
            neo4j_session
        )
        GraphJob.from_node_schema(ScalewayDnsZoneSchema(), scoped_job_parameters).run(
            neo4j_session
        )
