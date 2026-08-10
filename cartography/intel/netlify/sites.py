import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.site import NetlifySiteSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_sites(
    neo4j_session: neo4j.Session,
    sites: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load the team's sites.

    Takes an already-fetched site list rather than fetching one: the entry point needs the list
    before this runs, to decide which deploy keys belong to the team and to load them first, since
    the `USES_DEPLOY_KEY` edge is resolved by a MATCH at site-load time.
    """
    transformed = transform_netlify_sites(sites)
    load_netlify_sites(neo4j_session, transformed, account_id, update_tag)
    cleanup_netlify_sites(neo4j_session, common_job_parameters)


@timeit
def get_netlify_sites(
    api_session: requests.Session,
    base_url: str,
    account_slug: str,
) -> list[dict[str, Any]]:
    return paginated_get(api_session, f"{base_url}/{account_slug}/sites")


def transform_netlify_sites(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Flatten `build_settings` onto the site and replace secrets with presence booleans.

    `build_settings` holds the git connection (provider, repo path, deploy key, build command)
    as a nested object, which Neo4j cannot store. Its `env` member is dropped: site environment
    variables are ingested as their own nodes, without values.

    `jwt_secret` is a signing secret, so only `has_jwt_secret` is kept.
    """
    transformed = []
    for site in sites:
        build_settings = site.get("build_settings") or {}
        transformed.append(
            {
                **site,
                "git_provider": site.get("git_provider")
                or build_settings.get("provider"),
                "repo_path": build_settings.get("repo_path"),
                "repo_url": build_settings.get("repo_url"),
                "repo_branch": build_settings.get("repo_branch"),
                "repo_allowed_branches": build_settings.get("allowed_branches"),
                "repo_public": build_settings.get("public_repo"),
                "repo_private_logs": build_settings.get("private_logs"),
                "repo_stop_builds": build_settings.get("stop_builds"),
                "build_command": build_settings.get("cmd"),
                "publish_dir": build_settings.get("dir"),
                "functions_dir": build_settings.get("functions_dir"),
                "deploy_key_id": build_settings.get("deploy_key_id"),
                "has_jwt_secret": bool(site.get("jwt_secret")),
            },
        )
    return transformed


@timeit
def load_netlify_sites(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifySiteSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_sites(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # Children of a deleted site are cleaned up by their own scoped jobs, which run before this
    # one in _sync_one_account: they are all anchored on the account, so a site disappearing
    # leaves its children stale and they are removed on the same pass.
    GraphJob.from_node_schema(NetlifySiteSchema(), common_job_parameters).run(
        neo4j_session,
    )
