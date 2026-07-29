from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.webhook import DopplerWebhookSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    project_slugs: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    webhooks = get(api_session, common_job_parameters["BASE_URL"], project_slugs)
    load_webhooks(
        neo4j_session,
        webhooks,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_slugs: list[str],
) -> list[dict[str, Any]]:
    # Only non-sensitive webhook metadata is kept; the `secret` field is dropped.
    webhooks: list[dict[str, Any]] = []
    for project in project_slugs:
        for webhook in paginated_get(
            api_session,
            f"{base_url}/webhooks",
            "webhooks",
            params={"project": project},
        ):
            webhooks.append(
                {
                    "id": webhook["id"],
                    "name": webhook.get("name"),
                    "url": webhook.get("url"),
                    "enabled": webhook.get("enabled"),
                    "project": project,
                }
            )
    return webhooks


@timeit
def load_webhooks(
    neo4j_session: neo4j.Session,
    webhooks: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerWebhookSchema(),
        webhooks,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerWebhookSchema(), common_job_parameters).run(
        neo4j_session
    )
