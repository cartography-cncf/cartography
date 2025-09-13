import logging
from typing import Any
from typing import Tuple

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.keycloak.util import get_paginated
from cartography.models.keycloak.organization import KeycloakOrganizationSchema
from cartography.models.keycloak.organizationdomain import (
    KeycloakOrganizationDomainSchema,
)
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
    organizations = get(
        api_session,
        base_url,
        common_job_parameters["REALM"],
    )
    transformed_orgs, transformed_domains = transform(organizations)
    load_organizations(
        neo4j_session,
        transformed_orgs,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_org_domains(
        neo4j_session,
        transformed_domains,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


def transform(
    organizations: list[dict[str, Any]],
) -> Tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    transformed_orgs = []
    transformed_domains = {}
    for org in organizations:
        # Transform members to a list of IDs
        org["_managed_members"] = []
        org["_unmanaged_members"] = []
        for member in org.get("_members", []):
            if member.get("membershipType") == "UNMANAGED":
                org["_unmanaged_members"].append(member["id"])
            else:
                org["_managed_members"].append(member["id"])
        org.pop("_members", None)
        # Transform identity providers to a list of IDs
        org["_idp_ids"] = [
            idp["internalId"] for idp in org.get("_identity_providers", [])
        ]
        org.pop("_identity_providers", None)
        # Extract domains
        domains = org.get("domains", [])
        for domain in domains:
            domain_id = f"{org['id']}-{domain['name']}"
            transformed_domains[domain_id] = {
                "id": domain_id,
                "verified": domain.get("verified", False),
                "name": domain["name"],
                "organization_id": org["id"],
            }
        org.pop("domains", None)
        transformed_orgs.append(org)
    return transformed_orgs, list(transformed_domains.values())


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    realm: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    url = f"{base_url}/admin/realms/{realm}/organizations"
    for org in get_paginated(api_session, url):
        # Get members
        members_url = (
            f"{base_url}/admin/realms/{realm}/organizations/{org['id']}/members"
        )
        org["_members"] = list(
            get_paginated(
                api_session,
                members_url,
                params={"briefRepresentation": True},
            )
        )
        # Get Identity Providers
        idp_url = f"{base_url}/admin/realms/{realm}/organizations/{org['id']}/identity-providers"
        org["_identity_providers"] = list(
            get_paginated(
                api_session,
                idp_url,
                params={"briefRepresentation": True},
            )
        )
        result.append(org)
    return result


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Keycloak Organizations (%s) into Neo4j.", len(data), realm)
    load(
        neo4j_session,
        KeycloakOrganizationSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def load_org_domains(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Keycloak Organization Domains (%s) into Neo4j.", len(data), realm
    )
    load(
        neo4j_session,
        KeycloakOrganizationDomainSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        KeycloakOrganizationDomainSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(KeycloakOrganizationSchema(), common_job_parameters).run(
        neo4j_session
    )
