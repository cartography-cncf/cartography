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


def used_counts(response: dict[str, Any]) -> dict[str, int]:
    """
    Returns the account's current resource-in-use counts as reported by
    /v1/users/quotas (e.g. {"instances": 4, "volumes": 2, "service_groups": 1}).
    Used by other resource syncs to notice a truncated, unpaginated list response
    -- see util.check_count_matches().
    """
    quotas = (response.get("data") or {}).get("quotas") or []
    quota = quotas[0] if quotas else {}
    return quota.get("used") or {}


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
) -> tuple[str, dict[str, int]]:
    """
    :return: A tuple of (account id, the account's current used-resource counts).
    Deliberately does not call cleanup() here: this schema has no
    sub_resource_relationship today, but its cleanup must still run with a fully
    built common_job_parameters (including ACCOUNT_ID) once one exists, matching
    every other resource's cleanup call -- see start_unikraft_ingestion().
    """
    response = get_own_quotas(session, base_url)
    account = transform(response)
    load_account(neo4j_session, account, update_tag)
    return account["id"], used_counts(response)
