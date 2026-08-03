from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get_by_page
from cartography.models.anthropic.ratelimit import AnthropicRateLimitSchema
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    workspace_ids: list[str],
) -> None:
    rate_limits = transform_rate_limits(
        get(api_session, common_job_parameters["BASE_URL"]),
        workspace_id=None,
    )
    for workspace_id in workspace_ids:
        rate_limits.extend(
            transform_rate_limits(
                get_workspace_rate_limits(
                    api_session,
                    common_job_parameters["BASE_URL"],
                    workspace_id,
                ),
                workspace_id=workspace_id,
            )
        )
    load_rate_limits(
        neo4j_session,
        rate_limits,
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
        f"{base_url}/organizations/rate_limits",
        timeout=_TIMEOUT,
    )


@timeit
def get_workspace_rate_limits(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/workspaces/{workspace_id}/rate_limits",
        timeout=_TIMEOUT,
    )


def transform_rate_limits(
    groups: list[dict[str, Any]],
    workspace_id: str | None,
) -> list[dict[str, Any]]:
    """Explode each group's list of limits into one node per individual limit.

    The API returns limits as a nested list of objects, which Neo4j cannot store as
    a node property, and gives no identifier for either the group or the individual
    limit. The id is synthesised from the fields that make a limit unique: its scope,
    group type, models and limit type.
    """
    results: list[dict[str, Any]] = []
    for group in groups:
        group_type = group.get("group_type")
        models = group.get("models") or []
        scope = workspace_id or "organization"
        model_key = ",".join(sorted(models)) if models else "all"
        for limit in group.get("limits") or []:
            limit_type = limit.get("type")
            results.append(
                {
                    "id": f"{scope}/{group_type}/{model_key}/{limit_type}",
                    "group_type": group_type,
                    "limit_type": limit_type,
                    "value": limit.get("value"),
                    "org_limit": limit.get("org_limit"),
                    "models": models,
                    "workspace_id": workspace_id,
                }
            )
    return results


@timeit
def load_rate_limits(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicRateLimitSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AnthropicRateLimitSchema(), common_job_parameters).run(
        neo4j_session
    )
