import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_proxy_tokens
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.proxy_token import ModalProxyTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    raw = await list_proxy_tokens(client)
    tokens = transform(raw)
    load_proxy_tokens(
        neo4j_session,
        tokens,
        common_job_parameters["WORKSPACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return tokens


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(token) for token in raw]


@timeit
def load_proxy_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalProxyTokenSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalProxyTokenSchema(), common_job_parameters).run(
        neo4j_session
    )
