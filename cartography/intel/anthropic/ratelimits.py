import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get_by_page
from cartography.models.anthropic.ratelimit import AnthropicRateLimitSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    workspace_ids: list[str],
) -> None:
    org_id = common_job_parameters["ORG_ID"]
    rate_limits = transform_rate_limits(
        get(api_session, common_job_parameters["BASE_URL"]),
        workspace_id=None,
        org_id=org_id,
    )
    skipped_workspace_ids: list[str] = []
    for workspace_id in workspace_ids:
        try:
            workspace_limits = get_workspace_rate_limits(
                api_session,
                common_job_parameters["BASE_URL"],
                workspace_id,
            )
        except requests.exceptions.HTTPError as exc:
            # A workspace the credential cannot read must not take the whole module
            # down, nor let cleanup converge its previously ingested limits to empty.
            logger.warning(
                "Skipping rate limits for Anthropic workspace %s: %s",
                workspace_id,
                exc,
            )
            skipped_workspace_ids.append(workspace_id)
            continue
        rate_limits.extend(
            transform_rate_limits(
                workspace_limits, workspace_id=workspace_id, org_id=org_id
            )
        )
    load_rate_limits(
        neo4j_session,
        rate_limits,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    if skipped_workspace_ids:
        # Cleanup is organization-scoped, so running it now would delete the limits of
        # every workspace that was skipped. Keep the last known good state instead.
        logger.warning(
            "Skipping Anthropic rate limit cleanup: %d workspace(s) could not be read "
            "(%s), and organization-scoped cleanup would delete their existing limits.",
            len(skipped_workspace_ids),
            ", ".join(skipped_workspace_ids),
        )
        return
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
    org_id: str,
) -> list[dict[str, Any]]:
    """Explode each group's list of limits into one node per individual limit.

    The API returns limits as a nested list of objects, which Neo4j cannot store as
    a node property, and gives no identifier for either the group or the individual
    limit. The id is synthesised from the fields that make a limit unique: the
    organization, the scope, the group type, the models and the limit type.

    The organization has to be part of it. An organization-wide limit has no workspace
    to distinguish it, so two organizations in the same graph would otherwise both
    produce `organization/...` and merge into a single node.
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
                    "id": f"{org_id}/{scope}/{group_type}/{model_key}/{limit_type}",
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
