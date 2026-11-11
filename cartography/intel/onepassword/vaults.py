import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.onepassword.users import is_service_account
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.onepassword.vault import OnePasswordGroupCanAccessVaultRel
from cartography.models.onepassword.vault import (
    OnePasswordServiceAccountCanAccessVaultRel,
)
from cartography.models.onepassword.vault import OnePasswordUserCanAccessVaultRel
from cartography.models.onepassword.vault import OnePasswordVaultSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

ACCOUNT_LABEL = "OnePasswordAccount"
GRANT_SCHEMAS: tuple[CartographyRelSchema, ...] = (
    OnePasswordUserCanAccessVaultRel(),
    OnePasswordServiceAccountCanAccessVaultRel(),
    OnePasswordGroupCanAccessVaultRel(),
)


def _grant(grant: dict[str, Any], principal_id: str) -> dict[str, Any]:
    return {
        "vault_id": grant["vault_id"],
        "principal_id": principal_id,
        "permissions": grant["permissions"],
        "permissions_bitmask": grant["permissions_bitmask"],
    }


def transform_vaults(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": vault["id"], "name": vault.get("name")} for vault in snapshot["vaults"]
    ]


def transform_grants(
    snapshot: dict[str, Any],
) -> list[tuple[CartographyRelSchema, list[dict[str, Any]]]]:
    """Pair vault grants with the relationship schema of the principal's node label."""
    service_account_ids = {
        user["id"] for user in snapshot["users"] if is_service_account(user)
    }
    user_grants: list[dict[str, Any]] = []
    service_account_grants: list[dict[str, Any]] = []
    for grant in snapshot["vault_user_grants"]:
        if grant["user_id"] in service_account_ids:
            service_account_grants.append(_grant(grant, grant["user_id"]))
        else:
            user_grants.append(_grant(grant, grant["user_id"]))
    group_grants = [
        _grant(grant, grant["group_id"]) for grant in snapshot["vault_group_grants"]
    ]
    return [
        (OnePasswordUserCanAccessVaultRel(), user_grants),
        (OnePasswordServiceAccountCanAccessVaultRel(), service_account_grants),
        (OnePasswordGroupCanAccessVaultRel(), group_grants),
    ]


def load_vaults(
    neo4j_session: neo4j.Session,
    vaults: list[dict[str, Any]],
    grants: list[tuple[CartographyRelSchema, list[dict[str, Any]]]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OnePasswordVaultSchema(),
        vaults,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    for schema, rows in grants:
        load_matchlinks(
            neo4j_session,
            schema,
            rows,
            lastupdated=update_tag,
            _sub_resource_label=ACCOUNT_LABEL,
            _sub_resource_id=account_id,
        )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OnePasswordVaultSchema(), common_job_parameters).run(
        neo4j_session,
    )
    for schema in GRANT_SCHEMAS:
        GraphJob.from_matchlink(
            schema,
            ACCOUNT_LABEL,
            common_job_parameters["ACCOUNT_ID"],
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    snapshot: dict[str, Any],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    vaults = transform_vaults(snapshot)
    grants = transform_grants(snapshot)
    load_vaults(neo4j_session, vaults, grants, snapshot["account_id"], update_tag)
    cleanup(neo4j_session, common_job_parameters)
