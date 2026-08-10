import logging
from typing import Any

import neo4j
import scaleway
from scaleway.function.v1beta1 import Function
from scaleway.function.v1beta1 import FunctionV1Beta1API
from scaleway.function.v1beta1 import Namespace
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.serverless.function import (
    ScalewayServerlessFunctionSchema,
)
from cartography.models.scaleway.serverless.function_namespace import (
    ScalewayServerlessFunctionNamespaceSchema,
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
    namespaces, functions = get(client, org_id)
    namespaces_by_project, functions_by_project = transform(namespaces, functions)
    load_functions(
        neo4j_session, namespaces_by_project, functions_by_project, update_tag
    )
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Namespace], list[Function]]:
    api = FunctionV1Beta1API(client)
    namespaces = list_all_regions(api.list_namespaces_all, organization_id=org_id)
    # Functions can only be listed per-namespace (namespace_id is required); the
    # namespace already knows its region, so query each one directly.
    functions: list[Function] = []
    for namespace in namespaces:
        # A namespace can be deleted between the list and this per-namespace
        # call; skip it on a 404 rather than aborting the whole sync, but let
        # any other API error surface.
        try:
            functions.extend(
                api.list_functions_all(
                    region=namespace.region, namespace_id=namespace.id
                )
            )
        except ScalewayException as exc:
            if exc.status_code == 404:
                logger.warning(
                    "Skipping Scaleway functions for namespace %s: not found (%s).",
                    namespace.id,
                    exc,
                )
                continue
            raise
    return namespaces, functions


def transform(
    namespaces: list[Namespace],
    functions: list[Function],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    namespaces_by_project: dict[str, list[dict[str, Any]]] = {}
    functions_by_project: dict[str, list[dict[str, Any]]] = {}

    # Functions inherit the project of their parent namespace: the API does not
    # return project_id on them.
    project_by_namespace_id = {ns.id: ns.project_id for ns in namespaces}

    for namespace in namespaces:
        namespaces_by_project.setdefault(namespace.project_id, []).append(
            scaleway_obj_to_dict(namespace)
        )

    for function in functions:
        project_id = project_by_namespace_id.get(function.namespace_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway function %s: unknown parent namespace %s.",
                function.id,
                function.namespace_id,
            )
            continue
        functions_by_project.setdefault(project_id, []).append(
            scaleway_obj_to_dict(function)
        )

    return namespaces_by_project, functions_by_project


@timeit
def load_functions(
    neo4j_session: neo4j.Session,
    namespaces_by_project: dict[str, list[dict[str, Any]]],
    functions_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, namespaces in namespaces_by_project.items():
        logger.info(
            "Loading %d Scaleway function namespaces in project '%s' into Neo4j.",
            len(namespaces),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayServerlessFunctionNamespaceSchema(),
            namespaces,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, functions in functions_by_project.items():
        load(
            neo4j_session,
            ScalewayServerlessFunctionSchema(),
            functions,
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
        # Children before parent: Function -> FunctionNamespace.
        GraphJob.from_node_schema(
            ScalewayServerlessFunctionSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayServerlessFunctionNamespaceSchema(), scoped_job_parameters
        ).run(neo4j_session)
