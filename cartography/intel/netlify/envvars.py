import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import NetlifyPlanGatedError
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.envvar import NetlifyEnvVarSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Marks the team-wide pass in the composite id, so a team-wide FOO and a site-scoped FOO stay
# distinct nodes.
_ACCOUNT_SCOPE_SENTINEL = "_account"


@timeit
def sync_netlify_env_vars(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync the team-wide environment variables and then each site's own.

    Team-wide (shared) variables are a paid feature. A Free team was observed to answer the
    team-wide call with `200 []` rather than a 403, so the plan-gated branch is defensive: it
    covers a token without team-wide scope, or a plan tier that does reject the call.

    When it does trigger, the deletion pass has to be held back. Team-wide and site-scoped
    variables share one cleanup scope, so a skipped team-wide pass means the ingested set is no
    longer exhaustive for that scope, and a team that lost access to shared variables would
    otherwise have the ones a previous run ingested deleted. Site variables are still loaded,
    since refreshing lastupdated is always safe; only the deletion is skipped.
    """
    raw: list[tuple[str | None, dict[str, Any]]] = []
    cleanup_safe = True
    try:
        raw.extend(
            (None, env_var)
            for env_var in get_netlify_env_vars(api_session, base_url, account_id)
        )
    except NetlifyPlanGatedError:
        logger.warning(
            "Netlify team-wide environment variables are not available to this token or plan. "
            "Site-scoped variables are still synced, but the environment variable cleanup is "
            "skipped for this run so that previously ingested shared variables survive.",
        )
        cleanup_safe = False

    for site in sites:
        raw.extend(
            (site["id"], env_var)
            for env_var in get_netlify_env_vars(
                api_session,
                base_url,
                account_id,
                site_id=site["id"],
            )
        )
    env_vars = transform_netlify_env_vars(raw, account_id)
    load_netlify_env_vars(neo4j_session, env_vars, account_id, update_tag)
    if cleanup_safe:
        cleanup_netlify_env_vars(neo4j_session, common_job_parameters)


@timeit
def get_netlify_env_vars(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    site_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch environment variables for the team, or for one site when `site_id` is given.

    Netlify's OpenAPI spec also documents `GET /sites/{site_id}/env`, but that path is
    double-prefixed in the spec and 404s in practice: `?site_id=` on the account endpoint is the
    working route for site-scoped variables.

    :raises NetlifyPlanGatedError: on a 403. The caller decides what that means for its cleanup;
        it is never silently an empty result.
    """
    params = {"site_id": site_id} if site_id else None
    return paginated_get(
        api_session,
        f"{base_url}/accounts/{account_id}/env",
        params=params,
    )


def transform_netlify_env_vars(
    raw: list[tuple[str | None, dict[str, Any]]],
    account_id: str,
) -> list[dict[str, Any]]:
    """
    Drop every value, keep the contexts they were set for, and build the composite id.

    Netlify returns a secret's value masked down to its last four characters and a non-secret's
    value in full. Neither is ingested. `is_secret_flag` mirrors `is_secret` as a string because
    conditional extra labels are compared as Cypher strings.
    """
    env_vars = []
    for site_id, env_var in raw:
        values = env_var.get("values") or []
        updated_by = env_var.get("updated_by") or {}
        scope_key = site_id or _ACCOUNT_SCOPE_SENTINEL
        is_secret = bool(env_var.get("is_secret"))
        env_vars.append(
            {
                "id": f"{account_id}|{scope_key}|{env_var['key']}",
                "key": env_var["key"],
                "site_id": site_id,
                "scope": "site" if site_id else "account",
                "scopes": env_var.get("scopes"),
                "contexts": sorted(
                    {v["context"] for v in values if v.get("context")},
                ),
                "is_secret": is_secret,
                "is_secret_flag": "true" if is_secret else "false",
                "updated_at": env_var.get("updated_at"),
                "updated_by_user_id": updated_by.get("id"),
            },
        )
    return env_vars


@timeit
def load_netlify_env_vars(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyEnvVarSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_env_vars(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyEnvVarSchema(), common_job_parameters).run(
        neo4j_session,
    )
