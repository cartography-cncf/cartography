import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
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

    Team-wide (shared) variables are a paid feature, so that first call may come back 403 on a
    Free team. Since the team-wide and site-scoped variables land in the same cleanup scope, a
    plan-gated 403 must not be mistaken for "the team has none": paginated_get returns an empty
    list in that case, which is the correct answer, because Netlify only creates shared
    variables once the plan allows them.
    """
    raw: list[tuple[str | None, dict[str, Any]]] = [
        (None, env_var)
        for env_var in get_netlify_env_vars(api_session, base_url, account_id)
    ]
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
    """
    params = {"site_id": site_id} if site_id else None
    return paginated_get(
        api_session,
        f"{base_url}/accounts/{account_id}/env",
        params=params,
        allow_plan_gated=True,
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
