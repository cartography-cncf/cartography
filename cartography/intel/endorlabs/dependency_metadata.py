import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.endorlabs.util import paginated_get
from cartography.models.endorlabs.dependency_metadata import (
    EndorLabsDependencyMetadataSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get(bearer_token: str, namespace: str) -> list[dict[str, Any]]:
    return paginated_get(bearer_token, namespace, "dependency-metadata")


def transform(
    raw_deps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    deps = []
    for dep in raw_deps:
        meta = dep.get("meta", {})
        spec = dep.get("spec", {})
        importer_data = spec.get("importer_data", {})
        dependency_data = spec.get("dependency_data", {})

        deps.append(
            {
                "uuid": dep["uuid"],
                "name": meta.get("name"),
                "namespace": dep.get("tenant_meta", {}).get("namespace"),
                "direct": dependency_data.get("direct"),
                "reachable": dependency_data.get("reachable"),
                "scope": dependency_data.get("scope"),
                "project_uuid": importer_data.get("project_uuid"),
                "importer_uuid": meta.get("parent_uuid"),
                "dependency_name": meta.get("name"),
                "dependency_package_version_uuid": dependency_data.get(
                    "package_version_uuid",
                ),
            },
        )
    return deps


@timeit
def load_dependency_metadata(
    neo4j_session: neo4j.Session,
    deps: list[dict[str, Any]],
    namespace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EndorLabsDependencyMetadataSchema(),
        deps,
        lastupdated=update_tag,
        NAMESPACE_ID=namespace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        EndorLabsDependencyMetadataSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_dependency_metadata(
    neo4j_session: neo4j.Session,
    bearer_token: str,
    namespace: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    logger.info("Starting Endor Labs dependency metadata sync")
    raw_deps = get(bearer_token, namespace)
    deps = transform(raw_deps)
    load_dependency_metadata(neo4j_session, deps, namespace, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info(
        "Completed Endor Labs dependency metadata sync (%d records)",
        len(deps),
    )
    return deps
