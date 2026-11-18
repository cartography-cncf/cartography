import logging
from collections import defaultdict
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentra import api
from cartography.models.sentra.policy import SentraPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, api_url: str) -> Iterator[list[dict[str, Any]]]:
    yield from api.iter_search_pages(session, api_url, api.POLICIES_SEARCH_PATH)


def transform(
    raw_policies: list[dict[str, Any]],
    data_classes: Iterable[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """
    Shape policies for ingestion.

    Sentra names the data classes that a policy checks for, or their categories,
    but not their IDs. `data_classes` are the organization's transformed data
    classes, used to resolve those names to the IDs of `CLASSIFICATION` links.
    """
    ids_by_name: dict[str, set[str]] = defaultdict(set)
    ids_by_category: dict[str, set[str]] = defaultdict(set)
    for data_class in data_classes:
        ids_by_name[data_class["name"]].add(data_class["id"])
        if data_class.get("category"):
            ids_by_category[data_class["category"]].add(data_class["id"])

    result: list[dict[str, Any]] = []
    for policy in raw_policies:
        affected = policy.get("affected_data_classes") or {}
        class_names = affected.get("data_classes") or []
        categories = affected.get("categories") or []
        classification_ids: set[str] = set()
        for name in class_names:
            classification_ids |= ids_by_name.get(name, set())
        for category in categories:
            classification_ids |= ids_by_category.get(category, set())
        result.append(
            {
                "id": policy["id"],
                "name": policy["name"],
                "description": policy.get("description"),
                "canonical": policy["canonical"],
                "revision": policy["revision"],
                "severity": policy["severity"],
                "status": policy["status"],
                "policy_type": policy["type"],
                "risk_type": policy.get("risk_type"),
                "alert_type": policy.get("alert_type"),
                "entity_type": policy.get("entity_type"),
                "triggering_type": policy.get("triggering_type"),
                "predefined": policy["predefined"],
                "frameworks": policy.get("frameworks") or [],
                "tags": policy.get("tags") or [],
                "recommendation": policy.get("recommendation"),
                "remediation_actions": policy.get("remediation_actions") or [],
                "auto_approval": policy.get("auto_approval"),
                "affected_data_classes": class_names,
                "affected_data_class_categories": categories,
                "classification_data_class_ids": sorted(classification_ids),
                "opened_alerts": policy.get("opened_alerts"),
                "created_at": policy.get("created_at"),
            },
        )
    return result


@timeit
def load_policies(
    neo4j_session: neo4j.Session,
    data: Iterable[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentraPolicySchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentraPolicySchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    data_classes: list[dict[str, Any]],
) -> None:
    logger.info("Syncing Sentra policies for organization %s", tenant_id)
    policies = (
        policy
        for page in get(session, api_url)
        for policy in transform(page, data_classes)
    )
    load_policies(neo4j_session, policies, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
