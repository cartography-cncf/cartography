import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.models.netlify.snippet import NetlifySnippetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_snippets(
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
        raw_by_site[site["id"]] = get_netlify_snippets(
            api_session,
            base_url,
            site["id"],
        )
    snippets = transform_netlify_snippets(raw_by_site)
    load_netlify_snippets(neo4j_session, snippets, account_id, update_tag)
    cleanup_netlify_snippets(neo4j_session, common_job_parameters)


@timeit
def get_netlify_snippets(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    return get_list(api_session, f"{base_url}/sites/{site_id}/snippets")


def transform_netlify_snippets(
    raw_by_site: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Scope the snippet id to its site.

    Netlify's snippet id is the snippet's position in the site's list, so it collides across
    sites and is not stable across deletions: removing the first snippet renumbers every one
    after it. Scoping to the site fixes the collision; the renumbering means a delete can look
    to cleanup like an edit of the survivors plus a removal of the last index, which is
    acceptable because the node count still ends up right.
    """
    snippets = []
    for site_id, site_snippets in raw_by_site.items():
        for snippet in site_snippets:
            snippet_index = snippet["id"]
            snippets.append(
                {
                    **snippet,
                    "id": f"{site_id}|{snippet_index}",
                    "snippet_index": snippet_index,
                    "site_id": site_id,
                },
            )
    return snippets


@timeit
def load_netlify_snippets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifySnippetSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_snippets(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifySnippetSchema(), common_job_parameters).run(
        neo4j_session,
    )
