from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.account import DatabricksAccountSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    common_job_parameters: dict[str, Any],
) -> str:
    """Load the DatabricksAccount node and return its id (the account id)."""
    account = {
        "id": api_session.account_id,
        "account_id": api_session.account_id,
        "host": api_session.host,
    }
    load(
        neo4j_session,
        DatabricksAccountSchema(),
        [account],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return api_session.account_id


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksAccountSchema(), common_job_parameters).run(
        neo4j_session
    )
