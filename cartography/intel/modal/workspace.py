import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.intel.modal.util import get_workspace
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.workspace import ModalWorkspaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
) -> dict[str, Any]:
    """Ingest the workspace the credentials authenticate against.

    Returns the workspace row so the caller can scope everything else to it. There is no
    cleanup: see the note on ModalWorkspaceSchema.
    """
    raw = await get_workspace(client)
    workspace = transform(raw)
    load_workspace(neo4j_session, [workspace], common_job_parameters["UPDATE_TAG"])
    return workspace


def transform(raw: dict[str, Any]) -> dict[str, Any]:
    # The adapter already returns the exact shape the schema expects, so this is a
    # pass-through. It exists so tests can exercise the same seam as every other resource.
    return dict(raw)


@timeit
def load_workspace(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalWorkspaceSchema(),
        data,
        lastupdated=update_tag,
    )
