import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.unikraft.util import require_non_empty
from cartography.models.unikraft.account import UnikraftAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_own_quotas(session: requests.Session, base_url: str) -> dict[str, Any]:
    response = session.get(f"{base_url}/v1/users/quotas", timeout=(60, 60))
    response.raise_for_status()
    return response.json()


def transform(response: dict[str, Any]) -> dict[str, Any]:
    quotas = (response.get("data") or {}).get("quotas") or []
    quota = quotas[0] if quotas else {}
    return {
        "id": require_non_empty(quota.get("uuid"), "account uuid"),
        "status": quota.get("status"),
        "message": quota.get("message"),
    }


@timeit
def load_account(
    neo4j_session: neo4j.Session,
    data: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UnikraftAccountSchema(),
        [data],
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UnikraftAccountSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> str:
    response = get_own_quotas(session, base_url)
    account = transform(response)
    load_account(neo4j_session, account, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return account["id"]
