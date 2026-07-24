from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.project_role import DopplerProjectRoleSchema
from cartography.models.doppler.workplace_role import DopplerWorkplaceRoleSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    workplace_roles, project_roles = get(api_session, common_job_parameters["BASE_URL"])
    load_roles(
        neo4j_session,
        workplace_roles,
        project_roles,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    workplace_roles = paginated_get(api_session, f"{base_url}/workplace/roles", "roles")
    project_roles = paginated_get(api_session, f"{base_url}/projects/roles", "roles")
    return workplace_roles, project_roles


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    workplace_roles: list[dict[str, Any]],
    project_roles: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerWorkplaceRoleSchema(),
        workplace_roles,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )
    load(
        neo4j_session,
        DopplerProjectRoleSchema(),
        project_roles,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerWorkplaceRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(DopplerProjectRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
