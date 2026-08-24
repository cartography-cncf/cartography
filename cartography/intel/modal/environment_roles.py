import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import get_environment_roles
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.environment_role import ModalEnvironmentRoleSchema
from cartography.models.modal.environment_role import (
    ModalServiceUserToEnvironmentRoleMatchLink,
)
from cartography.models.modal.environment_role import (
    ModalUserToEnvironmentRoleMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Modal's per-environment roles are a fixed builtin set derived from the ENVIRONMENT_ROLE_*
# enum rather than listed by the API.
_ENVIRONMENT_ROLE_NAMES = {
    "ENVIRONMENT_ROLE_VIEWER": "viewer",
    "ENVIRONMENT_ROLE_CONTRIBUTOR": "contributor",
    "ENVIRONMENT_ROLE_NO_ACCESS": "no-access",
}


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Ingest one environment's role nodes and the principal bindings onto them.

    Note this is the only environment-scoped call that keys on the environment *id* rather
    than its name.
    """
    environment_id = common_job_parameters["ENVIRONMENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    raw = await get_environment_roles(client, environment_id)

    roles = transform_roles(environment_id)
    load_roles(neo4j_session, roles, environment_id, update_tag)

    member_bindings, service_user_bindings = transform_bindings(raw, environment_id)
    load_bindings(
        neo4j_session,
        member_bindings,
        service_user_bindings,
        environment_id,
        update_tag,
    )

    cleanup(neo4j_session, common_job_parameters)
    return raw


def transform_roles(environment_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{environment_id}/{name}",
            "name": name,
            "scope": "environment",
        }
        for name in sorted(_ENVIRONMENT_ROLE_NAMES.values())
    ]


def transform_bindings(
    raw: list[dict[str, Any]], environment_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split the principal list into member bindings and service user bindings.

    Exactly one of user_id / service_user_id is set on each principal.
    """
    member_bindings = []
    service_user_bindings = []
    for principal in raw:
        role_name = _ENVIRONMENT_ROLE_NAMES.get(principal.get("role") or "")
        if not role_name:
            logger.debug(
                "Skipping Modal principal with unmapped environment role %s",
                principal.get("role"),
            )
            continue
        role_id = f"{environment_id}/{role_name}"
        if principal.get("user_id"):
            member_bindings.append(
                {"user_id": principal["user_id"], "role_id": role_id}
            )
        elif principal.get("service_user_id"):
            service_user_bindings.append(
                {"service_user_id": principal["service_user_id"], "role_id": role_id}
            )
    return member_bindings, service_user_bindings


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalEnvironmentRoleSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def load_bindings(
    neo4j_session: neo4j.Session,
    member_bindings: list[dict[str, Any]],
    service_user_bindings: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    if member_bindings:
        load_matchlinks(
            neo4j_session,
            ModalUserToEnvironmentRoleMatchLink(),
            member_bindings,
            lastupdated=update_tag,
            _sub_resource_label="ModalEnvironment",
            _sub_resource_id=environment_id,
        )
    if service_user_bindings:
        load_matchlinks(
            neo4j_session,
            ModalServiceUserToEnvironmentRoleMatchLink(),
            service_user_bindings,
            lastupdated=update_tag,
            _sub_resource_label="ModalEnvironment",
            _sub_resource_id=environment_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    _cleanup_environment(
        neo4j_session,
        common_job_parameters,
        common_job_parameters["ENVIRONMENT_ID"],
    )


def _cleanup_environment(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    environment_id: str,
) -> None:
    """Remove stale roles and bindings scoped to one environment.

    Bindings are cleaned before the role nodes: the MatchLink cleanups are scoped through
    the environment, and deleting the role nodes first would leave nothing for them to
    match on.
    """
    update_tag = common_job_parameters["UPDATE_TAG"]
    GraphJob.from_matchlink(
        ModalUserToEnvironmentRoleMatchLink(),
        "ModalEnvironment",
        environment_id,
        update_tag,
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        ModalServiceUserToEnvironmentRoleMatchLink(),
        "ModalEnvironment",
        environment_id,
        update_tag,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        ModalEnvironmentRoleSchema(),
        {**common_job_parameters, "ENVIRONMENT_ID": environment_id},
    ).run(neo4j_session)


@timeit
def cleanup_for_environment(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    environment_id: str,
    update_tag: int,
) -> None:
    """Tear down this resource's data for one environment, by id.

    Called by the environment sync's cascade when an environment disappears from Modal. See
    ``cartography.intel.modal.environments`` for why that cascade is needed.
    """
    _cleanup_environment(
        neo4j_session,
        {"UPDATE_TAG": update_tag, "WORKSPACE_ID": workspace_id},
        environment_id,
    )
