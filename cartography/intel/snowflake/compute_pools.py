import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.compute_pool import SnowflakeComputePoolSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """List compute pools, or None when the account cannot answer.

    Snowpark Container Services is not enabled on every account or in every
    region, and listing pools needs a privilege a read-only role may not hold.
    Either way Snowflake answers 403 or 404, which must not fail the whole sync.
    """
    try:
        return client.list_all("/api/v2/compute-pools")
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform(
    compute_pools: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for pool in compute_pools:
        name = pool["name"]
        transformed.append(
            {
                "id": sf_id(account_id, "compute_pool", sf_fqn(name)),
                "name": name,
                "state": pool.get("state"),
                "min_nodes": pool.get("min_nodes"),
                "max_nodes": pool.get("max_nodes"),
                "active_nodes": pool.get("active_nodes"),
                "instance_family": pool.get("instance_family"),
                "num_services": pool.get("num_services"),
                "num_jobs": pool.get("num_jobs"),
                "is_exclusive": pool.get("is_exclusive"),
                "application": pool.get("application"),
                "auto_resume": pool.get("auto_resume"),
                "auto_suspend_secs": pool.get("auto_suspend_secs"),
                "owner": pool.get("owner"),
                "comment": pool.get("comment"),
                "created_on": iso_to_datetime(pool.get("created_on")),
            },
        )
    return transformed


def load_compute_pools(
    neo4j_session: neo4j.Session,
    compute_pools: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeComputePoolSchema(),
        compute_pools,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeComputePoolSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake compute pools.

    Runs before services so a service's WORKLOAD_PARENT edge resolves against a
    pool node already in the graph.
    """
    raw_compute_pools = get(client)
    if raw_compute_pools is None:
        warn_unavailable(
            "compute pools",
            "Snowpark Container Services is unavailable or not permitted",
        )
        return False

    compute_pools = transform(raw_compute_pools, client.account_id)
    logger.info(
        "Loading %d Snowflake compute pools for account %s.",
        len(compute_pools),
        client.account_id,
    )
    load_compute_pools(
        neo4j_session,
        compute_pools,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
