import logging
from typing import Any

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.domain import Domain

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.entra.utils import (
    get_paginated_values_with_expired_page_retry,
)
from cartography.models.microsoft.entra.domain import EntraDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def domain_name_of(user_principal_name: str | None) -> str | None:
    """Return the lowercase domain of a user principal name, or None without one.

    Graph matches domains case-insensitively, so names are lowercased on both
    sides of the user to domain link.
    """
    if not user_principal_name or "@" not in user_principal_name:
        return None
    return user_principal_name.rsplit("@", 1)[1].lower()


@timeit
async def get_domains(client: GraphServiceClient) -> list[Domain]:
    return await get_paginated_values_with_expired_page_retry(
        client.domains.get,
        lambda url: client.domains.with_url(url).get(),
        "domains",
    )


def transform_domains(domains: list[Domain], tenant_id: str) -> list[dict[str, Any]]:
    result = []
    for domain in domains:
        if not domain.id:
            continue
        name = domain.id.lower()
        result.append(
            {
                "id": f"{tenant_id}/{name}",
                "name": name,
                "authentication_type": domain.authentication_type,
                "is_default": domain.is_default,
                "is_initial": domain.is_initial,
                "is_root": domain.is_root,
                "is_verified": domain.is_verified,
                "is_admin_managed": domain.is_admin_managed,
                "supported_services": domain.supported_services,
            }
        )
    return result


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    domains: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EntraDomainSchema(),
        domains,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup_domains(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(EntraDomainSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync_entra_domains(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str | None,
    client_secret: str | None,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    *,
    delegated_auth: bool = False,
    access_token: str | None = None,
) -> None:
    """Sync the tenant's domains. Runs before users, which link to them."""
    credential = credentials.make_credential(
        tenant_id,
        client_id,
        client_secret,
        delegated_auth=delegated_auth,
        access_token=access_token,
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    domains = await get_domains(client)
    load_domains(
        neo4j_session, transform_domains(domains, tenant_id), tenant_id, update_tag
    )

    if not delegated_auth:
        cleanup_domains(neo4j_session, common_job_parameters)
