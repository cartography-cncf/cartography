import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.keycloak.util import get_paginated
from cartography.models.keycloak.identityprovider import KeycloakIdentityProviderSchema
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
) -> None:
    identityproviders = get(
        api_session,
        base_url,
        common_job_parameters["REALM"],
    )
    idps_transformed = transform(identityproviders)
    load_identityproviders(
        neo4j_session,
        idps_transformed,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    realm: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    url = f"{base_url}/admin/realms/{realm}/identity-provider/instances"
    for idp in get_paginated(api_session, url, params={"briefRepresentation": False}):
        # Get members
        members_url = f"{base_url}/admin/realms/{realm}/users"
        idp["_members"] = list(
            get_paginated(
                api_session,
                members_url,
                params={"idpAlias": idp["alias"], "briefRepresentation": True},
            )
        )
        result.append(idp)
    return result


def transform(idps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for idp in idps:
        idp["_member_ids"] = [member["id"] for member in idp["_members"]]
        idp.pop("_members", None)
    return idps


@timeit
def load_identityproviders(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Keycloak IdentityProviders (%s) into Neo4j.", len(data), realm
    )
    load(
        neo4j_session,
        KeycloakIdentityProviderSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        KeycloakIdentityProviderSchema(), common_job_parameters
    ).run(neo4j_session)
