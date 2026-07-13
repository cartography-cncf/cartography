import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.account_service_principal import (
    DatabricksAccountServicePrincipalSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    sps = get(api_session)
    transformed = transform(sps, account_id)
    load_service_principals(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.scim_list(api_session.account_uri("/scim/v2/ServicePrincipals"))


@timeit
def transform(sps: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for sp in sps:
        scim_id = sp.get("id")
        # A blank SCIM id would collapse to the account-scoped key
        # "{account_id}/" and merge distinct malformed records onto one node;
        # skip rather than corrupt graph identity.
        if not scim_id:
            logger.warning(
                "Skipping Databricks account service principal with empty SCIM id."
            )
            continue
        result.append(
            {
                "id": account_scoped_id(account_id, scim_id),
                "scim_id": scim_id,
                "application_id": sp.get("applicationId"),
                "display_name": sp.get("displayName"),
                "external_id": sp.get("externalId"),
                "active": sp.get("active"),
                "group_ids": [
                    account_scoped_id(account_id, g["value"])
                    for g in (sp.get("groups") or [])
                    if g.get("value")
                ],
            }
        )
    return result


@timeit
def load_service_principals(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksAccountServicePrincipalSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksAccountServicePrincipalSchema(), common_job_parameters
    ).run(neo4j_session)
