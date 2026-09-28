import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.warehouse import SnowflakeWarehouseSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    return client.list_all("/api/v2/warehouses")


def transform(
    warehouses: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for warehouse in warehouses:
        name = warehouse["name"]
        resource_monitor = warehouse.get("resource_monitor")
        transformed.append(
            {
                "id": sf_id(account_id, "warehouse", sf_fqn(name)),
                "name": name,
                "warehouse_type": warehouse.get("warehouse_type"),
                # Snowflake spells the size field `size` on some API versions and
                # `warehouse_size` on others; both mean the same thing.
                "size": warehouse.get("size") or warehouse.get("warehouse_size"),
                "state": warehouse.get("state"),
                "min_cluster_count": warehouse.get("min_cluster_count"),
                "max_cluster_count": warehouse.get("max_cluster_count"),
                "scaling_policy": warehouse.get("scaling_policy"),
                "auto_suspend": warehouse.get("auto_suspend"),
                "auto_resume": warehouse.get("auto_resume"),
                "resource_monitor": resource_monitor or None,
                # Null when the warehouse has no monitor, which suppresses the
                # MONITORED_BY edge instead of pointing it at a nonexistent node.
                "resource_monitor_id": (
                    sf_id(account_id, "resource_monitor", sf_fqn(resource_monitor))
                    if resource_monitor
                    else None
                ),
                "enable_query_acceleration": warehouse.get("enable_query_acceleration"),
                "max_concurrency_level": warehouse.get("max_concurrency_level"),
                "statement_timeout_in_seconds": warehouse.get(
                    "statement_timeout_in_seconds"
                ),
                "owner": warehouse.get("owner"),
                "owner_role_type": warehouse.get("owner_role_type"),
                "budget": warehouse.get("budget"),
                "kind": warehouse.get("kind"),
                "comment": warehouse.get("comment"),
                "created_on": iso_to_datetime(warehouse.get("created_on")),
                "resumed_on": iso_to_datetime(warehouse.get("resumed_on")),
                "updated_on": iso_to_datetime(warehouse.get("updated_on")),
            },
        )
    return transformed


def load_warehouses(
    neo4j_session: neo4j.Session,
    warehouses: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeWarehouseSchema(),
        warehouses,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeWarehouseSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake virtual warehouses.

    Runs after resource monitors so the MONITORED_BY edge resolves on the first
    pass. Returns True: the account-level listing either succeeds or raises, so
    there is no partial state to protect.
    """
    warehouses = transform(get(client), client.account_id)
    logger.info(
        "Loading %d Snowflake warehouses for account %s.",
        len(warehouses),
        client.account_id,
    )
    load_warehouses(
        neo4j_session,
        warehouses,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
