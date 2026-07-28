import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.storage.volume import RailwayVolumeSchema
from cartography.models.railway.storage.volumeinstance import (
    RailwayVolumeInstanceSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

_MB_PER_GB = 1024


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    update_tag: int,
) -> None:
    volumes, volume_instances = transform(bundles)
    load_volumes(neo4j_session, volumes, update_tag)
    load_volume_instances(neo4j_session, volume_instances, update_tag)
    cleanup(neo4j_session, list(bundles), common_job_parameters)


def transform(
    bundles: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    volumes: dict[str, list[dict[str, Any]]] = {}
    volume_instances: dict[str, list[dict[str, Any]]] = {}

    for project_id, bundle in bundles.items():
        project_volumes = unwrap_edges(bundle["volumes"])
        volumes[project_id] = project_volumes
        # The instance is the BlockStorage node, but only the parent volume carries a name,
        # so denormalise it: _ont_name must be a name, not a mount path.
        volume_names = {volume["id"]: volume.get("name") for volume in project_volumes}

        project_instances: list[dict[str, Any]] = []
        for environment in unwrap_edges(bundle["environments"]):
            for instance in unwrap_edges(environment["volumeInstances"]):
                size_mb = instance.get("sizeMB")
                project_instances.append(
                    {
                        **instance,
                        # The BlockStorage ontology speaks in GB; Railway reports MB.
                        "size_gb": (
                            size_mb / _MB_PER_GB if size_mb is not None else None
                        ),
                        "volume_name": volume_names.get(instance.get("volumeId")),
                    },
                )
        volume_instances[project_id] = project_instances

    return volumes, volume_instances


@timeit
def load_volumes(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, volumes in by_project.items():
        load(
            neo4j_session,
            RailwayVolumeSchema(),
            volumes,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def load_volume_instances(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, instances in by_project.items():
        load(
            neo4j_session,
            RailwayVolumeInstanceSchema(),
            instances,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    project_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in project_ids:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        # Children before parents: instances hang off volumes.
        GraphJob.from_node_schema(
            RailwayVolumeInstanceSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            RailwayVolumeSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
