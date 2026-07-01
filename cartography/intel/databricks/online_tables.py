import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.online_table import DatabricksOnlineTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    candidates = get_candidate_tables(neo4j_session, workspace_id)
    online_tables = get(api_session, candidates)
    transformed = transform(online_tables)
    load_online_tables(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get_candidate_tables(
    neo4j_session: neo4j.Session, workspace_id: str
) -> list[dict[str, Any]]:
    """Return managed UC tables to probe for an online-table twin.

    The online-tables API only has get-by-name (no list), so we probe managed
    tables already in the graph. ponytail: one GET per managed table; if this
    ever bites on a huge metastore, gate it behind a config flag.
    """
    query = """
    MATCH (:DatabricksWorkspace {id: $workspace_id})-[:RESOURCE]->(t:DatabricksTable)
    WHERE t.table_type = 'MANAGED'
    RETURN t.full_name AS full_name, t.metastore_id AS metastore_id
    """
    result = neo4j_session.run(query, workspace_id=workspace_id)
    return [dict(record) for record in result]


@timeit
def get(
    api_session: DatabricksWorkspaceClient, candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    online_tables: list[dict[str, Any]] = []
    for c in candidates:
        full_name = c.get("full_name")
        if not full_name:
            continue
        try:
            ot = api_session.get(f"/api/2.0/online-tables/{full_name}")
        except requests.HTTPError as e:
            # 404 = the table has no online-table twin, which is the common
            # case. Any other error (auth, rate-limit, 5xx) must abort so
            # cleanup does not run on partial data.
            skip_or_raise_http(e, 404)
            continue
        if ot.get("name"):
            ot["_metastore_id"] = c.get("metastore_id")
            online_tables.append(ot)
    return online_tables


@timeit
def transform(online_tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for ot in online_tables:
        name = ot["name"]
        # Always injected from the source table's graph row in get().
        metastore_id = str(ot["_metastore_id"])
        spec = ot.get("spec") or {}
        status = ot.get("status") or {}
        source_full_name = spec.get("source_table_full_name")
        result.append(
            {
                "id": uc_id(metastore_id, name),
                "name": name,
                "metastore_id": metastore_id,
                "source_table_full_name": source_full_name,
                "source_table_id": (
                    uc_id(metastore_id, source_full_name) if source_full_name else None
                ),
                "pipeline_id": spec.get("pipeline_id"),
                "detailed_state": status.get("detailed_state"),
                "provisioning_state": ot.get("unity_catalog_provisioning_state"),
                "table_serving_url": ot.get("table_serving_url"),
                "primary_key_columns": spec.get("primary_key_columns"),
                "timeseries_key": spec.get("timeseries_key"),
            }
        )
    return result


@timeit
def load_online_tables(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksOnlineTableSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksOnlineTableSchema(), common_job_parameters).run(
        neo4j_session
    )
