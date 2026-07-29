import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import _TIMEOUT
from cartography.models.doppler.service_token import DopplerServiceTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    configs: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    tokens, fetch_complete = get(
        api_session, common_job_parameters["BASE_URL"], configs
    )
    load_service_tokens(
        neo4j_session,
        tokens,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    # Only prune stale tokens if the fetch was trustworthy; see secrets.sync for why.
    if fetch_complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping DopplerServiceToken cleanup: no config token fetch succeeded "
            "this run, preserving existing data."
        )


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    configs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """Returns (tokens, fetch_complete). fetch_complete is False only when there were
    configs to query but every per-config fetch failed."""
    tokens: list[dict[str, Any]] = []
    success = False
    for config in configs:
        # Best-effort per config: a single inaccessible/missing config (e.g. a 404)
        # should not halt service-token ingestion for every other config.
        try:
            req = api_session.get(
                f"{base_url}/configs/config/tokens",
                params={"project": config["project"], "config": config["config"]},
                timeout=_TIMEOUT,
            )
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.warning(
                "Failed to fetch service tokens for Doppler config %s, skipping: %s",
                config["config_id"],
                e,
            )
            continue
        success = True
        for token in req.json().get("tokens", []) or []:
            token["config_id"] = config["config_id"]
            tokens.append(token)
    return tokens, (success or not configs)


@timeit
def load_service_tokens(
    neo4j_session: neo4j.Session,
    tokens: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerServiceTokenSchema(),
        tokens,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerServiceTokenSchema(), common_job_parameters).run(
        neo4j_session
    )
