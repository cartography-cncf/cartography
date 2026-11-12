import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.onepassword.group import OnePasswordGroupSchema

logger = logging.getLogger(__name__)


def transform(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"id": group["id"], "name": group["name"]} for group in snapshot["groups"]]


def load_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OnePasswordGroupSchema(),
        groups,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OnePasswordGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )
