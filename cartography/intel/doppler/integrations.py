from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.integration import DopplerIntegrationSchema
from cartography.models.doppler.secret_sync import DopplerSecretSyncSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    integrations = get(api_session, common_job_parameters["BASE_URL"])
    integrations, secret_syncs = transform(integrations)
    load_integrations(
        neo4j_session,
        integrations,
        secret_syncs,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return paginated_get(api_session, f"{base_url}/integrations", "integrations")


def transform(
    integrations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # Secret syncs are embedded in each integration's `syncs` array; lift them out
    # into their own records linked back to the integration and target config.
    secret_syncs: list[dict[str, Any]] = []
    for integration in integrations:
        for s in integration.pop("syncs", []) or []:
            project = s.get("project")
            config = s.get("config")
            secret_syncs.append(
                {
                    "slug": s.get("slug"),
                    "enabled": s.get("enabled"),
                    "last_synced_at": s.get("lastSyncedAt"),
                    "integration_slug": integration["slug"],
                    "config_id": (
                        f"{project}/{config}" if project and config else None
                    ),
                }
            )
    return integrations, secret_syncs


@timeit
def load_integrations(
    neo4j_session: neo4j.Session,
    integrations: list[dict[str, Any]],
    secret_syncs: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerIntegrationSchema(),
        integrations,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )
    load(
        neo4j_session,
        DopplerSecretSyncSchema(),
        secret_syncs,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerIntegrationSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(DopplerSecretSyncSchema(), common_job_parameters).run(
        neo4j_session
    )
