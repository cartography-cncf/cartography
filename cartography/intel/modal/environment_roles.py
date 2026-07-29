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
    ModalWorkspaceMemberToEnvironmentRoleMatchLink,
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
            ModalWorkspaceMemberToEnvironmentRoleMatchLink(),
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
    environment_id = common_job_parameters["ENVIRONMENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]
    GraphJob.from_matchlink(
        ModalWorkspaceMemberToEnvironmentRoleMatchLink(),
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
    GraphJob.from_node_schema(ModalEnvironmentRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
