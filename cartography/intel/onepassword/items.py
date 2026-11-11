import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.onepassword.item import OnePasswordItemSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def transform(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "vault_id": item["vault_id"],
            "title": item.get("title"),
            "category": item.get("category"),
            "state": item.get("state"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "version": item.get("version"),
        }
        for item in snapshot["items"]
    ]


def load_items(
    neo4j_session: neo4j.Session,
    items: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OnePasswordItemSchema(),
        items,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OnePasswordItemSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    snapshot: dict[str, Any],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    items = transform(snapshot)
    load_items(neo4j_session, items, snapshot["account_id"], update_tag)
    cleanup(neo4j_session, common_job_parameters)
