import logging
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentra import api
from cartography.models.sentra.data_class import SentraDataClassSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, api_url: str) -> Iterator[list[dict[str, Any]]]:
    yield from api.iter_search_pages(session, api_url, api.DATA_CLASSES_SEARCH_PATH)


def transform(raw_classes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": data_class["id"],
            "name": data_class["name"],
            "description": data_class.get("description"),
            "category": data_class.get("category"),
            "class_type": data_class.get("type"),
            "source": data_class.get("source"),
            "enabled": data_class.get("enabled"),
            "experimental": data_class.get("experimental"),
            "is_ai": data_class.get("is_ai"),
            "sensitivity_weight": data_class.get("sensitivity_weight"),
            "findings_count": data_class.get("findings_count"),
            "created_at": data_class.get("created_at"),
        }
        for data_class in raw_classes
    ]


@timeit
def load_data_classes(
    neo4j_session: neo4j.Session,
    data: Iterable[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentraDataClassSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentraDataClassSchema(), common_job_parameters).run(
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
) -> list[dict[str, Any]]:
    """Sync data classes and return them, so policies can link to them by name."""
    logger.info("Syncing Sentra data classes for organization %s", tenant_id)
    data_classes = [
        data_class for page in get(session, api_url) for data_class in transform(page)
    ]
    load_data_classes(neo4j_session, data_classes, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return data_classes
