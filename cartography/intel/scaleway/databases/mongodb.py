import logging
from typing import Any

import neo4j
import scaleway
from scaleway.mongodb.v1 import Instance
from scaleway.mongodb.v1 import MongodbV1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.database.mongodb_instance import (
    ScalewayMongoDBInstanceSchema,
)
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
    instances = get(client, org_id)
    instances_by_project = transform_instances(instances)
    load_instances(neo4j_session, instances_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(client: scaleway.Client, org_id: str) -> list[Instance]:
    api = MongodbV1API(client)
    return list_all_regions(api.list_instances_all, organization_id=org_id)


def transform_instances(
    instances: list[Instance],
) -> dict[str, list[dict[str, Any]]]:
    instances_by_project: dict[str, list[dict[str, Any]]] = {}
    for instance in instances:
        formatted = scaleway_obj_to_dict(instance)
        _flatten_mongo_endpoints(formatted)
        _flatten_mongo_volume(formatted)
        instances_by_project.setdefault(instance.project_id, []).append(formatted)
    return instances_by_project


def _flatten_mongo_endpoints(formatted: dict[str, Any]) -> None:
    """Flatten the MongoDB endpoints list into scalar public/private fields.

    A MongoDB endpoint is either ``public_network`` (publicly reachable, with a
    DNS record) or ``private_network`` (reachable from a VPC private network,
    also via a DNS record).
    """
    endpoints = formatted.get("endpoints") or []
    is_public = False
    public_dns: str | None = None
    public_port: int | None = None
    private_dns: str | None = None
    private_port: int | None = None
    private_network_ids: list[str] = []

    for endpoint in endpoints:
        dns_record = endpoint.get("dns_record")
        port = endpoint.get("port")
        if endpoint.get("public_network") is not None:
            is_public = True
            if public_dns is None:
                public_dns = dns_record
                public_port = port
        elif endpoint.get("private_network") is not None:
            pn = endpoint["private_network"]
            pn_id = pn.get("private_network_id")
            if pn_id:
                private_network_ids.append(pn_id)
            if private_dns is None:
                private_dns = dns_record
                private_port = port

    formatted["is_public"] = is_public
    formatted["public_endpoint_dns"] = public_dns
    formatted["public_endpoint_port"] = public_port
    formatted["private_endpoint_dns"] = private_dns
    formatted["private_endpoint_port"] = private_port
    formatted["private_network_ids"] = private_network_ids or None


def _flatten_mongo_volume(formatted: dict[str, Any]) -> None:
    volume = formatted.get("volume") or {}
    formatted["volume_type"] = volume.get("type_")
    formatted["volume_size"] = volume.get("size_bytes")


@timeit
def load_instances(
    neo4j_session: neo4j.Session,
    instances_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, instances in instances_by_project.items():
        logger.info(
            "Loading %d Scaleway MongoDB instances in project '%s' into Neo4j.",
            len(instances),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayMongoDBInstanceSchema(),
            instances,
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
        GraphJob.from_node_schema(
            ScalewayMongoDBInstanceSchema(), scoped_job_parameters
        ).run(neo4j_session)
