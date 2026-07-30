import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.models.netlify.function import NetlifyFunctionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Netlify abbreviates every key in the nested `functions` array. Mapping documented against a
# live response; the published OpenAPI spec still claims `{id, name, sha, region}`.
_FUNCTION_FIELDS = {
    "n": "name",
    "id": "provider_function_id",
    "d": "content_digest",
    "r": "runtime",
    "rg": "region",
    "m": "memory_mb",
    "s": "size_bytes",
    "im": "invocation_mode",
    "a": "provider_account_id",
    "c": "created_at",
    "endpoint": "endpoint",
    "schedule": "schedule",
}


@timeit
def sync_netlify_functions(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_by_site: dict[str, list[dict[str, Any]]] = {}
    for site in sites:
        raw_by_site[site["id"]] = get_netlify_functions(
            api_session,
            base_url,
            site["id"],
        )
    functions = transform_netlify_functions(raw_by_site)
    load_netlify_functions(neo4j_session, functions, account_id, update_tag)
    cleanup_netlify_functions(neo4j_session, common_job_parameters)


@timeit
def get_netlify_functions(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    """
    Fetch the function bundles deployed on a site.

    This endpoint is not paginated and, unlike the rest of the API, answers with a bare object
    instead of a one-element array when the site has a single bundle. A site with no functions
    answers `200 {}`, not a 404, whether or not it has ever been deployed: verified against the
    live API on a site created with no functions and again after deploying it without any.
    get_list() normalises both shapes to a list.
    """
    return get_list(api_session, f"{base_url}/sites/{site_id}/functions")


def transform_netlify_functions(
    raw_by_site: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Flatten the per-branch bundles into one row per function and expand the abbreviated keys.

    Netlify groups functions by branch, so the same function name appears once per branch. The
    node id is `<site_id>|<branch>|<name>`: the inner `id` and `d` fields are content hashes
    that change on every build, so keying on them would create a new node per deploy.
    """
    functions: dict[str, dict[str, Any]] = {}
    for site_id, bundles in raw_by_site.items():
        for bundle in bundles:
            branch = bundle.get("branch")
            for raw in bundle.get("functions") or []:
                function = {
                    long_name: raw.get(short_name)
                    for short_name, long_name in _FUNCTION_FIELDS.items()
                }
                # The name composes the node id, so read it directly: a `.get()` would turn an
                # unexpected payload into an id of "<site>|<branch>|None" instead of failing.
                function["name"] = raw["n"]
                function["site_id"] = site_id
                function["branch"] = branch
                function["provider"] = bundle.get("provider")
                function["log_type"] = bundle.get("log_type")
                function["id"] = f"{site_id}|{branch}|{function['name']}"
                # Netlify has been observed to repeat a name within one bundle; last one wins,
                # matching how the platform itself resolves the route.
                functions[function["id"]] = function
    return list(functions.values())


@timeit
def load_netlify_functions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyFunctionSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_functions(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyFunctionSchema(), common_job_parameters).run(
        neo4j_session,
    )
