from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.doppler.util import _TIMEOUT
from cartography.models.doppler.workplace import DopplerWorkplaceSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> str:
    workplace = get(api_session, common_job_parameters["BASE_URL"])
    load_workplace(neo4j_session, workplace, common_job_parameters["UPDATE_TAG"])
    return workplace["id"]


@timeit
def get(api_session: requests.Session, base_url: str) -> dict[str, Any]:
    req = api_session.get(f"{base_url}/workplace", timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()["workplace"]


@timeit
def load_workplace(
    neo4j_session: neo4j.Session,
    workplace: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerWorkplaceSchema(),
        [workplace],
        lastupdated=update_tag,
    )
