import logging
from typing import Any

import neo4j
import scaleway
from scaleway.rdb.v1 import Instance
from scaleway.rdb.v1 import RdbV1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.database.rdb_instance import ScalewayRdbInstanceSchema
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
    api = RdbV1API(client)
    return list_all_regions(api.list_instances_all, organization_id=org_id)


def transform_instances(
    instances: list[Instance],
) -> dict[str, list[dict[str, Any]]]:
    instances_by_project: dict[str, list[dict[str, Any]]] = {}
    for instance in instances:
        formatted = scaleway_obj_to_dict(instance)
        _flatten_rdb_endpoints(formatted)
        _flatten_rdb_extras(formatted)
        instances_by_project.setdefault(instance.project_id, []).append(formatted)
    return instances_by_project


def _flatten_rdb_endpoints(formatted: dict[str, Any]) -> None:
    """Flatten the RDB endpoints list into scalar public/private fields.

    Scaleway RDB exposes endpoints in three flavours: ``load_balancer`` (managed
    public endpoint with a routable IP/hostname), ``direct_access`` (legacy
    direct public IP on the node), and ``private_network`` (reachable only from
    a VPC private network). The first two are publicly reachable; the third is
    not.
    """
    endpoints = formatted.get("endpoints") or []
    is_public = False
    public_ip: str | None = None
    public_hostname: str | None = None
    public_port: int | None = None
    private_ip: str | None = None
    private_port: int | None = None
    private_network_ids: list[str] = []

    for endpoint in endpoints:
        if endpoint.get("private_network"):
            pn_id = endpoint["private_network"].get("private_network_id")
            if pn_id:
                private_network_ids.append(pn_id)
            if private_ip is None:
                private_ip = endpoint.get("ip")
                private_port = endpoint.get("port")
        elif (
            endpoint.get("load_balancer") is not None
            or endpoint.get("direct_access") is not None
        ):
            is_public = True
            if public_ip is None and public_hostname is None:
                public_ip = endpoint.get("ip")
                public_hostname = endpoint.get("hostname")
                public_port = endpoint.get("port")

    formatted["is_public"] = is_public
    formatted["public_endpoint_ip"] = public_ip
    formatted["public_endpoint_hostname"] = public_hostname
    formatted["public_endpoint_port"] = public_port
    formatted["private_endpoint_ip"] = private_ip
    formatted["private_endpoint_port"] = private_port
    formatted["private_network_ids"] = private_network_ids or None


def _flatten_rdb_extras(formatted: dict[str, Any]) -> None:
    """Flatten nested encryption/backup/volume objects into scalar fields."""
    encryption = formatted.get("encryption") or {}
    formatted["encryption_at_rest_enabled"] = encryption.get("enabled")

    volume = formatted.get("volume") or {}
    formatted["volume_type"] = volume.get("type_")
    formatted["volume_size"] = volume.get("size")

    backup = formatted.get("backup_schedule") or {}
    formatted["backup_schedule_disabled"] = backup.get("disabled")
    # Scaleway exposes retention as a duration string ("604800s"); normalise to
    # days when parseable, otherwise leave the raw value for visibility.
    retention = backup.get("retention")
    formatted["backup_schedule_retention_days"] = _retention_to_days(retention)


def _retention_to_days(retention: Any) -> int | None:
    if retention is None:
        return None
    if isinstance(retention, (int, float)):
        return int(retention) // 86400
    s = str(retention).strip()
    if s.endswith("s"):
        s = s[:-1]
    try:
        return int(float(s)) // 86400
    except ValueError:
        return None


@timeit
def load_instances(
    neo4j_session: neo4j.Session,
    instances_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, instances in instances_by_project.items():
        logger.info(
            "Loading %d Scaleway RDB instances in project '%s' into Neo4j.",
            len(instances),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayRdbInstanceSchema(),
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
            ScalewayRdbInstanceSchema(), scoped_job_parameters
        ).run(neo4j_session)
