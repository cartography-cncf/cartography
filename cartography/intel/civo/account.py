import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.civo.util import _TIMEOUT
from cartography.intel.civo.util import require_non_empty
from cartography.models.civo.account import CivoAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> dict[str, Any]:
    account = get(api_session, common_job_parameters["BASE_URL"])
    require_non_empty(account.get("id"), "account id")
    load_accounts(neo4j_session, [account], common_job_parameters["UPDATE_TAG"])
    return account


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> dict[str, Any]:
    req = api_session.get(
        f"{base_url}/v2/quota",
        timeout=_TIMEOUT,
    )
    req.raise_for_status()
    return req.json()


@timeit
def load_accounts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CivoAccountSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CivoAccountSchema(), common_job_parameters).run(
        neo4j_session,
    )
