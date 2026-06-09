from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.portkey.util import list_admin_users
from cartography.models.portkey.organization import PortkeyOrganizationSchema
from cartography.models.portkey.user import PortkeyUserSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    users = list_admin_users(api_session, common_job_parameters["BASE_URL"])
    load_users(
        neo4j_session,
        users,
        common_job_parameters["PORTKEY_ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        PortkeyOrganizationSchema(),
        [{"id": org_id}],
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        PortkeyUserSchema(),
        data,
        lastupdated=update_tag,
        PORTKEY_ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(PortkeyUserSchema(), common_job_parameters).run(
        neo4j_session
    )
