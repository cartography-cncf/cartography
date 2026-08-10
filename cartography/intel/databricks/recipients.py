from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.recipient import DatabricksRecipientSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    metastore_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    recipients = get(api_session)
    transformed = transform(recipients, metastore_id)
    load_recipients(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.uc_list("/api/2.1/unity-catalog/recipients", "recipients")


@timeit
def transform(
    recipients: list[dict[str, Any]], metastore_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for r in recipients:
        name = r["name"]
        if not name:
            raise ValueError("Databricks recipient returned with empty name")
        result.append(
            {
                "id": uc_id(metastore_id, name),
                "name": name,
                "metastore_id": metastore_id,
                "authentication_type": r.get("authentication_type"),
                "activated": r.get("activated"),
                "owner": r.get("owner"),
                "comment": r.get("comment"),
                "data_recipient_global_metastore_id": r.get(
                    "data_recipient_global_metastore_id"
                ),
                "cloud": r.get("cloud"),
                "region": r.get("region"),
                "created_at": epoch_ms_to_datetime(r.get("created_at")),
                "created_by": r.get("created_by"),
                "updated_at": epoch_ms_to_datetime(r.get("updated_at")),
                "updated_by": r.get("updated_by"),
            }
        )
    return result


@timeit
def load_recipients(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksRecipientSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksRecipientSchema(), common_job_parameters).run(
        neo4j_session
    )
