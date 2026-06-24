import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import _TIMEOUT
from cartography.models.doppler.secret import DopplerSecretSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    configs: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    secrets, fetch_complete = get(
        api_session, common_job_parameters["BASE_URL"], configs
    )
    load_secrets(
        neo4j_session,
        secrets,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    # Only prune stale secrets if the fetch was trustworthy. If every config fetch
    # failed, `secrets` is [] not because there are none but because we could not see
    # them, and cleanup would wipe previously-ingested secrets.
    if fetch_complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping DopplerSecret cleanup: no config secret fetch succeeded this "
            "run, preserving existing data."
        )


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    configs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """Returns (secret name records, fetch_complete). fetch_complete is False only when
    there were configs to query but every per-config fetch failed."""
    # Use the names-only endpoint so secret VALUES are never pulled into the process.
    secrets: list[dict[str, Any]] = []
    success = False
    for config in configs:
        project, name, config_id = (
            config["project"],
            config["config"],
            config["config_id"],
        )
        # Best-effort per config: a single inaccessible/missing config (e.g. a 404)
        # should not halt secret-name ingestion for every other config.
        try:
            req = api_session.get(
                f"{base_url}/configs/config/secrets/names",
                params={"project": project, "config": name},
                timeout=_TIMEOUT,
            )
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.warning(
                "Failed to fetch secret names for Doppler config %s, skipping: %s",
                config_id,
                e,
            )
            continue
        success = True
        for secret_name in req.json().get("names", []) or []:
            secrets.append(
                {
                    "id": f"{config_id}/{secret_name}",
                    "name": secret_name,
                    "project": project,
                    "config": name,
                    "config_id": config_id,
                }
            )
    return secrets, (success or not configs)


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    secrets: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerSecretSchema(),
        secrets,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerSecretSchema(), common_job_parameters).run(
        neo4j_session
    )
