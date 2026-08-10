import logging
from typing import Any

import neo4j
import scaleway
from scaleway.key_manager.v1alpha1 import Key
from scaleway.key_manager.v1alpha1 import KeyManagerV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.kms.key import ScalewayKeySchema
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
    keys = get(client, org_id)
    keys_by_project = transform_keys(keys)
    load_keys(neo4j_session, keys_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Key]:
    api = KeyManagerV1Alpha1API(client)
    return list_all_regions(
        api.list_keys_all,
        organization_id=org_id,
        scheduled_for_deletion=False,
    )


def transform_keys(keys: list[Key]) -> dict[str, list[dict[str, Any]]]:
    keys_by_project: dict[str, list[dict[str, Any]]] = {}
    for key in keys:
        formatted_key = scaleway_obj_to_dict(key)
        # `usage` is a one-of holder with three optional sub-fields, exactly
        # one of which is set to a non-"unknown_*" algorithm. Neo4j can't
        # store the nested map, so flatten it.
        usage_type, usage_algorithm = _flatten_key_usage(formatted_key.get("usage"))
        formatted_key["usage_type"] = usage_type
        formatted_key["usage_algorithm"] = usage_algorithm
        rotation = formatted_key.get("rotation_policy") or {}
        formatted_key["rotation_period"] = rotation.get("rotation_period")
        formatted_key["rotation_next_at"] = rotation.get("next_rotation_at")
        keys_by_project.setdefault(key.project_id, []).append(formatted_key)
    return keys_by_project


def _flatten_key_usage(usage: Any) -> tuple[str | None, str | None]:
    if not isinstance(usage, dict):
        return None, None
    for usage_type, algorithm in usage.items():
        if isinstance(algorithm, str) and not algorithm.startswith("unknown_"):
            return usage_type, algorithm
    return None, None


@timeit
def load_keys(
    neo4j_session: neo4j.Session,
    keys_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, keys in keys_by_project.items():
        logger.info(
            "Loading %d Scaleway Keys in project '%s' into Neo4j.",
            len(keys),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayKeySchema(),
            keys,
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
        GraphJob.from_node_schema(ScalewayKeySchema(), scoped_job_parameters).run(
            neo4j_session
        )
