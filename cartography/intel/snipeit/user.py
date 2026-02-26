import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.pagination import get_pagination_limits
from cartography.models.snipeit.tenant import SnipeitTenantSchema
from cartography.models.snipeit.user import SnipeitUserSchema
from cartography.util import timeit

from .util import call_snipeit_api

logger = logging.getLogger(__name__)
MAX_PAGINATION_PAGES, MAX_PAGINATION_ITEMS = get_pagination_limits(logger)


@timeit
def get(base_uri: str, token: str) -> List[Dict]:
    api_endpoint = "/api/v1/users"
    results: List[Dict[str, Any]] = []
    offset = 0
    page_size = 500
    page_count = 0
    while True:
        if page_count >= MAX_PAGINATION_PAGES:
            logger.warning(
                "Snipe-IT: reached max pagination pages (%d). Stopping with %d users.",
                MAX_PAGINATION_PAGES,
                len(results),
            )
            break

        response = call_snipeit_api(
            f"{api_endpoint}?order=asc&offset={offset}&limit={page_size}",
            base_uri,
            token,
        )
        rows = response.get("rows", [])
        results.extend(rows)
        page_count += 1

        if len(results) > MAX_PAGINATION_ITEMS:
            logger.warning(
                "Snipe-IT: reached max pagination items (%d). Stopping after %d pages.",
                MAX_PAGINATION_ITEMS,
                page_count,
            )
            break

        total = response.get("total", 0)
        if len(results) >= total or not rows:
            break
        offset += len(rows)

    return results


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    data: List[Dict[str, Any]],
) -> None:
    logger.debug(data[0])

    # Create the SnipeIT Tenant
    load(
        neo4j_session,
        SnipeitTenantSchema(),
        [{"id": common_job_parameters["TENANT_ID"]}],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )

    load(
        neo4j_session,
        SnipeitUserSchema(),
        data,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        TENANT_ID=common_job_parameters["TENANT_ID"],
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(SnipeitUserSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    base_uri: str,
    token: str,
) -> None:
    users = get(base_uri=base_uri, token=token)
    load_users(neo4j_session, common_job_parameters, users)
    cleanup(neo4j_session, common_job_parameters)
