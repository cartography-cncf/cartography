import logging
from typing import Any

import neo4j
import scaleway
from scaleway.iot.v1 import Device
from scaleway.iot.v1 import Hub
from scaleway.iot.v1 import IotV1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.iot.hub import ScalewayIotDeviceSchema
from cartography.models.scaleway.iot.hub import ScalewayIotHubSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    hubs, devices_by_hub = get(client, org_id)
    hubs_by_project, devices_by_project = transform(hubs, devices_by_hub, projects_id)
    load_hubs(neo4j_session, hubs_by_project, devices_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Hub], dict[str, list[Device]]]:
    api = IotV1API(client)
    hubs = list_all_regions(api.list_hubs_all, organization_id=org_id)
    devices_by_hub: dict[str, list[Device]] = {}
    for hub in hubs:
        devices_by_hub[hub.id] = api.list_devices_all(hub_id=hub.id, region=hub.region)
    return hubs, devices_by_hub


def transform(
    hubs: list[Hub],
    devices_by_hub: dict[str, list[Device]],
    projects_id: list[str],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    # Cleanup is scoped to the projects returned by the project sync - see
    # webhosting.py's transform_hostings() for the same guard and rationale.
    known_projects = set(projects_id)
    hubs_by_project: dict[str, list[dict[str, Any]]] = {}
    devices_by_project: dict[str, list[dict[str, Any]]] = {}
    for hub in hubs:
        if hub.project_id not in known_projects:
            logger.warning(
                "Skipping Scaleway IoT Hub '%s': its project '%s' is not part of "
                "the synced organization projects.",
                hub.id,
                hub.project_id,
            )
            continue
        hubs_by_project.setdefault(hub.project_id, []).append(scaleway_obj_to_dict(hub))
        for device in devices_by_hub.get(hub.id, []):
            devices_by_project.setdefault(hub.project_id, []).append(
                scaleway_obj_to_dict(device)
            )
    return hubs_by_project, devices_by_project


@timeit
def load_hubs(
    neo4j_session: neo4j.Session,
    hubs_by_project: dict[str, list[dict[str, Any]]],
    devices_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, hubs in hubs_by_project.items():
        logger.info(
            "Loading %d Scaleway IoT Hubs in project '%s' into Neo4j.",
            len(hubs),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayIotHubSchema(),
            hubs,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, devices in devices_by_project.items():
        load(
            neo4j_session,
            ScalewayIotDeviceSchema(),
            devices,
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
        # Devices before hubs.
        GraphJob.from_node_schema(ScalewayIotDeviceSchema(), scoped_job_parameters).run(
            neo4j_session
        )
        GraphJob.from_node_schema(ScalewayIotHubSchema(), scoped_job_parameters).run(
            neo4j_session
        )
