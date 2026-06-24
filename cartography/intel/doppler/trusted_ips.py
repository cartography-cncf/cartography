import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import _TIMEOUT
from cartography.models.doppler.trusted_ip import DopplerTrustedIPSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    configs: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    trusted_ips, fetch_complete = get(
        api_session, common_job_parameters["BASE_URL"], configs
    )
    load_trusted_ips(
        neo4j_session,
        trusted_ips,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    # Only prune stale trusted IPs if the fetch was trustworthy; see secrets.sync.
    if fetch_complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping DopplerTrustedIP cleanup: no config trusted-IP fetch succeeded "
            "this run, preserving existing data."
        )


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    configs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """Returns (trusted IP records, fetch_complete). fetch_complete is False only when
    there were configs to query but every per-config fetch failed."""
    trusted_ips: list[dict[str, Any]] = []
    success = False
    for config in configs:
        config_id = config["config_id"]
        # Best-effort per config: a single inaccessible/missing config (e.g. a 404)
        # should not halt trusted-IP ingestion for every other config.
        try:
            req = api_session.get(
                f"{base_url}/configs/config/trusted_ips",
                params={"project": config["project"], "config": config["config"]},
                timeout=_TIMEOUT,
            )
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.warning(
                "Failed to fetch trusted IPs for Doppler config %s, skipping: %s",
                config_id,
                e,
            )
            continue
        success = True
        for ip in req.json().get("ips", []) or []:
            trusted_ips.append(
                {"id": f"{config_id}/{ip}", "cidr": ip, "config_id": config_id}
            )
    return trusted_ips, (success or not configs)


@timeit
def load_trusted_ips(
    neo4j_session: neo4j.Session,
    trusted_ips: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerTrustedIPSchema(),
        trusted_ips,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerTrustedIPSchema(), common_job_parameters).run(
        neo4j_session
    )
