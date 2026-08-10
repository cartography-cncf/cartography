import logging
from typing import Any

import neo4j
import scaleway
from scaleway.serverless_sqldb.v1alpha1 import Database
from scaleway.serverless_sqldb.v1alpha1 import ServerlessSqldbV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.database.serverless_sql import (
    ScalewayServerlessSQLDatabaseSchema,
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
    databases = get(client, org_id)
    databases_by_project = transform_databases(databases)
    load_databases(neo4j_session, databases_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Database]:
    api = ServerlessSqldbV1Alpha1API(client)
    return list_all_regions(api.list_databases_all, organization_id=org_id)


def transform_databases(
    databases: list[Database],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for database in databases:
        formatted = scaleway_obj_to_dict(database)
        # `endpoint` is the connection URL; keep it as a scalar even if the SDK
        # ever wraps it in an object.
        endpoint = formatted.get("endpoint")
        if isinstance(endpoint, dict):
            formatted["endpoint"] = (
                endpoint.get("url") or endpoint.get("host") or endpoint.get("ip")
            )
        # Serverless SQL databases are exposed through a public connection
        # endpoint; flag it for exposure analysis like the other data services.
        formatted["is_public"] = formatted.get("endpoint") is not None
        result.setdefault(database.project_id, []).append(formatted)
    return result


@timeit
def load_databases(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, databases in data.items():
        load(
            neo4j_session,
            ScalewayServerlessSQLDatabaseSchema(),
            databases,
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
        scopped_job_parameters = common_job_parameters.copy()
        scopped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            ScalewayServerlessSQLDatabaseSchema(), scopped_job_parameters
        ).run(neo4j_session)
