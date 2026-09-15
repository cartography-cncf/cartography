import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_sandboxes
from cartography.intel.modal.util import list_sandboxes_v2
from cartography.intel.modal.util import MODAL_API_ERRORS
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.sandbox import ModalSandboxSchema
from cartography.models.modal.sandbox_tunnel import ModalSandboxTunnelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
    apps: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Ingest the live sandboxes of one environment, with their forwarded ports.

    Two listings are needed. `SandboxList` covers v1 sandboxes environment-wide; v2 sandboxes
    are not returned by it and come from `SandboxListV2`, which is per app, hence the fan-out
    over ``apps``.

    ``apps`` is None when the app listing itself failed. The v1 sandboxes are still ingested in
    that case, since they do not need it, but v2 cannot be enumerated so the run counts as
    partial and cleanup is skipped.
    """
    environment_name = common_job_parameters["ENVIRONMENT_NAME"]
    environment_id = common_job_parameters["ENVIRONMENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    raw, complete = await list_sandboxes(client, environment_name)

    if apps is None:
        logger.warning(
            "Modal app list unavailable for environment %s, so v2 sandboxes cannot be "
            "enumerated; ingesting v1 sandboxes only and skipping cleanup.",
            environment_name,
        )
        complete = False
    for app in apps or []:
        try:
            v2_raw, v2_complete = await list_sandboxes_v2(client, app["id"])
        except MODAL_API_ERRORS as exc:
            # v2 is opt-in and the RPC is authenticated differently, so a workspace that never
            # used it can legitimately refuse the call. Degrade to partial enumeration rather
            # than losing the v1 sandboxes we did read.
            logger.warning(
                "Could not list v2 sandboxes of Modal app %s: %s", app["id"], exc
            )
            complete = False
            continue
        raw.extend(v2_raw)
        complete = complete and v2_complete

    sandboxes = transform(raw, environment_name)
    load_sandboxes(neo4j_session, sandboxes, environment_id, update_tag)

    tunnels = transform_tunnels(raw, environment_name)
    load_tunnels(neo4j_session, tunnels, environment_id, update_tag)

    if complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping Modal sandbox cleanup for environment %s: at least one listing did not "
            "run to completion, so stale nodes are preserved rather than risk deleting live "
            "sandboxes.",
            environment_name,
        )
    return sandboxes


def transform(raw: list[dict[str, Any]], environment_name: str) -> list[dict[str, Any]]:
    sandboxes = []
    for sandbox in raw:
        # `tunnels` is a nested list consumed by transform_tunnels; it must not reach the
        # node loader, which only handles scalars and lists of scalars.
        tunnels = sandbox.get("tunnels") or []
        sandbox = {k: v for k, v in sandbox.items() if k != "tunnels"}
        # A tunnel is a forwarded port reachable from the public internet, so it is the
        # sandbox's inbound exposure. Per-tunnel TLS detail stays on ModalSandboxTunnel.
        sandboxes.append(
            {
                **sandbox,
                "environment_name": environment_name,
                "exposed_internet": bool(tunnels),
                "exposed_internet_type": ["direct"] if tunnels else None,
            }
        )
    return sandboxes


def transform_tunnels(
    raw: list[dict[str, Any]], environment_name: str
) -> list[dict[str, Any]]:
    tunnels = []
    for sandbox in raw:
        for tunnel in sandbox.get("tunnels") or []:
            tunnels.append(
                {
                    # Modal gives tunnels no id; the container port is unique per sandbox.
                    "id": f"{sandbox['id']}/{tunnel['container_port']}",
                    "sandbox_id": sandbox["id"],
                    "host": tunnel.get("host"),
                    "port": tunnel.get("port"),
                    "unencrypted_host": tunnel.get("unencrypted_host"),
                    "unencrypted_port": tunnel.get("unencrypted_port"),
                    # Precomputed so the cleartext-exposure case is directly queryable.
                    "has_unencrypted_endpoint": bool(tunnel.get("unencrypted_host")),
                    "container_port": tunnel["container_port"],
                    "environment_name": environment_name,
                }
            )
    return tunnels


@timeit
def load_sandboxes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalSandboxSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def load_tunnels(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalSandboxTunnelSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalSandboxTunnelSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ModalSandboxSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_for_environment(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    environment_id: str,
    update_tag: int,
) -> None:
    """Tear down this resource for one environment, by id. See `environments` for why."""
    cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": update_tag,
            "WORKSPACE_ID": workspace_id,
            "ENVIRONMENT_ID": environment_id,
        },
    )
