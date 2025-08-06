import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.keycloak.scope import KeycloakScopeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
    scope_ids: list[str],
) -> None:
    scope_mapping = get(
        api_session,
        base_url,
        common_job_parameters["REALM"],
        scope_ids,
    )
    transformed_scope_mapping = transform(scope_mapping)
    load_mapping(
        neo4j_session,
        transformed_scope_mapping,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    realm: str,
    scope_ids: list[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for scope_id in scope_ids:
        mappings_url = (
            f"{base_url}/admin/realms/{realm}/client-scopes/{scope_id}/scope-mappings"
        )
        req = api_session.get(
            mappings_url,
            timeout=_TIMEOUT,
        )
        result[scope_id] = req.json()
    return result


def transform(scopes: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for scope_id, mapping in scopes.items():
        for client_details in mapping.get("clientMappings", {}).values():
            for mapping in client_details.get("mappings", []):
                result.append(
                    {
                        "scope_id": scope_id,
                        "role_id": mapping["id"],
                    }
                )
        for realm_mapping in mapping.get("realmMappings", []):
            result.append(
                {
                    "scope_id": scope_id,
                    "role_id": realm_mapping["id"],
                }
            )
    return result


@timeit
def load_mapping(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    # WIP: use load_matchlink
    logger.info("Loading %d Keycloak Scopes (%s) into Neo4j.", len(data), realm)
    load(
        neo4j_session,
        KeycloakScopeSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # WIP: cleanup the REL
    GraphJob.from_node_schema(KeycloakScopeSchema(), common_job_parameters).run(
        neo4j_session
    )
