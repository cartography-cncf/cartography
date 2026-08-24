import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.models.netlify.serviceinstance import NetlifyServiceInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Provisioned credentials and pre-authenticated links the add-on API hands back.
_SECRET_KEYS = frozenset(
    {"config", "env", "auth_url", "external_attributes", "snippets"}
)


@timeit
def sync_netlify_service_instances(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_instances = []
    for site in sites:
        for instance in get_netlify_service_instances(
            api_session,
            base_url,
            site["id"],
        ):
            raw_instances.append({**instance, "site_id": site["id"]})
    instances = transform_netlify_service_instances(raw_instances)
    load_netlify_service_instances(neo4j_session, instances, account_id, update_tag)
    cleanup_netlify_service_instances(neo4j_session, common_job_parameters)


@timeit
def get_netlify_service_instances(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    return get_list(api_session, f"{base_url}/sites/{site_id}/service-instances")


def transform_netlify_service_instances(
    instances: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Strip everything the add-on provisioned.

    `config` and `env` hold the credentials the add-on injected into the site, `auth_url` is a
    pre-authenticated sign-in link, and `snippets` repeats markup already ingested as
    NetlifySnippet nodes.
    """
    return [
        {k: v for k, v in instance.items() if k not in _SECRET_KEYS}
        for instance in instances
    ]


@timeit
def load_netlify_service_instances(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyServiceInstanceSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_service_instances(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        NetlifyServiceInstanceSchema(),
        common_job_parameters,
    ).run(neo4j_session)
