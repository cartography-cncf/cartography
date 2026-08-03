from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get_by_page
from cartography.models.anthropic.serviceaccount import AnthropicServiceAccountSchema
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    service_accounts = get(api_session, common_job_parameters["BASE_URL"])
    for service_account in service_accounts:
        memberships = get_service_account_workspaces(
            api_session,
            common_job_parameters["BASE_URL"],
            service_account["id"],
        )
        transform_service_account(service_account, memberships)
    load_service_accounts(
        neo4j_session,
        service_accounts,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/service_accounts",
        timeout=_TIMEOUT,
    )


@timeit
def get_service_account_workspaces(
    api_session: requests.Session,
    base_url: str,
    service_account_id: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/service_accounts/{service_account_id}/workspaces",
        timeout=_TIMEOUT,
    )


def transform_service_account(
    service_account: dict[str, Any],
    memberships: list[dict[str, Any]],
) -> None:
    """Fold workspace memberships into id lists the relationships match on."""
    service_account["workspaces"] = [m["workspace_id"] for m in memberships]
    service_account["workspace_admins"] = [
        m["workspace_id"]
        for m in memberships
        if m["workspace_role"] == "workspace_admin"
    ]


@timeit
def load_service_accounts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicServiceAccountSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        AnthropicServiceAccountSchema(), common_job_parameters
    ).run(neo4j_session)
