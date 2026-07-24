import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.nullify.util import paginate
from cartography.models.nullify.user import NullifyUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    # /admin/users is not paginated; paginate() makes a single request when nextToken is absent.
    return paginate(api_session, f"{base_url}/admin/users", "users")


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NullifyUserSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(NullifyUserSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    users = get(api_session, base_url)
    load_users(neo4j_session, users, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return users
