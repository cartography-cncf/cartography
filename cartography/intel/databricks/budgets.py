import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.budget import DatabricksBudgetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    budgets = get(api_session)
    transformed = transform(budgets, account_id)
    load_budgets(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    """List account budget configurations.

    The budgets endpoint is a 2.1 API, so build the path manually since
    ``account_uri`` hardcodes 2.0. It paginates with ``next_page_token``, so walk
    every page via ``uc_list`` rather than returning only the first (otherwise
    later-page budgets would be omitted and then deleted by cleanup). Some
    accounts / regions do not expose the endpoint (returns 404); treat that as
    "no budgets" so the sync stays usable.
    """
    uri = f"/api/2.1/accounts/{api_session.account_id}/budgets"
    try:
        return api_session.uc_list(uri, key="budgets")
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            logger.info(
                "Databricks budgets endpoint not available for this account; skipping."
            )
            return []
        raise


@timeit
def transform(budgets: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for b in budgets:
        budget_configuration_id = b["budget_configuration_id"]
        result.append(
            {
                "id": account_scoped_id(account_id, budget_configuration_id),
                "budget_configuration_id": budget_configuration_id,
                "display_name": b.get("display_name"),
            }
        )
    return result


@timeit
def load_budgets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksBudgetSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksBudgetSchema(), common_job_parameters).run(
        neo4j_session
    )
