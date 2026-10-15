from typing import Iterator
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import pytest
from msgraph.generated.models.domain import Domain
from msgraph.generated.models.domain_collection_response import DomainCollectionResponse
from msgraph.generated.models.user import User
from msgraph.generated.models.user_collection_response import UserCollectionResponse
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

import cartography.intel.microsoft.entra.domains
import cartography.intel.microsoft.entra.users
from cartography.intel.microsoft.entra.domains import sync_entra_domains
from cartography.intel.microsoft.entra.users import load_tenant
from cartography.intel.microsoft.entra.users import sync_entra_users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TENANT_ID = "synthetic-domain-tenant"
OTHER_TENANT_ID = "synthetic-other-tenant"


@pytest.fixture(autouse=True)  # type: ignore[misc]
def isolated_graph(neo4j_session: neo4j.Session) -> Iterator[None]:
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n").consume()


def _graph_client(domains: list[Domain], users: list[User] | None = None) -> MagicMock:
    client = MagicMock()
    client.domains.get = AsyncMock(return_value=DomainCollectionResponse(value=domains))
    client.users.UsersRequestBuilderGetRequestConfiguration = (
        UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration
    )
    client.users.UsersRequestBuilderGetQueryParameters = (
        UsersRequestBuilder.UsersRequestBuilderGetQueryParameters
    )
    client.users.get = AsyncMock(return_value=UserCollectionResponse(value=users))
    client.reports.authentication_methods.user_registration_details.get = AsyncMock(
        return_value=None
    )
    client.identity_protection.risky_users.get = AsyncMock(return_value=None)
    return client


async def _sync_domains(
    neo4j_session: neo4j.Session, tenant_id: str, client: MagicMock, update_tag: int
) -> None:
    with patch.object(
        cartography.intel.microsoft.entra.domains,
        "GraphServiceClient",
        return_value=client,
    ):
        await sync_entra_domains(
            neo4j_session,
            tenant_id,
            "synthetic-client",
            "synthetic-secret",
            update_tag,
            {"UPDATE_TAG": update_tag, "TENANT_ID": tenant_id},
        )


async def _sync_users(
    neo4j_session: neo4j.Session, tenant_id: str, client: MagicMock, update_tag: int
) -> None:
    with patch.object(
        cartography.intel.microsoft.entra.users,
        "GraphServiceClient",
        return_value=client,
    ):
        await sync_entra_users(
            neo4j_session,
            tenant_id,
            "synthetic-client",
            "synthetic-secret",
            update_tag,
            {"UPDATE_TAG": update_tag, "TENANT_ID": tenant_id},
        )


@pytest.mark.asyncio  # type: ignore[misc]
async def test_users_link_to_their_own_tenants_domain(
    neo4j_session: neo4j.Session,
) -> None:
    """The same unverified domain can exist in two tenants; a user links only to
    the copy in its own tenant, and a user whose domain is not synced links to
    nothing."""
    # Arrange
    for tenant_id in (TENANT_ID, OTHER_TENANT_ID):
        load_tenant(neo4j_session, {"id": tenant_id}, 1)
    await _sync_domains(
        neo4j_session,
        OTHER_TENANT_ID,
        _graph_client([Domain(id="contoso.com", authentication_type="Managed")]),
        1,
    )
    client = _graph_client(
        [
            Domain(id="Contoso.com", authentication_type="Federated", is_verified=True),
            Domain(
                id="contoso.onmicrosoft.com",
                authentication_type="Managed",
                is_initial=True,
            ),
        ],
        [
            User(id="member", user_principal_name="alice@CONTOSO.com"),
            User(
                id="guest",
                user_principal_name="vendor_example.com#EXT#@contoso.onmicrosoft.com",
            ),
            User(id="unknown-domain", user_principal_name="bob@fabrikam.com"),
        ],
    )

    # Act
    await _sync_domains(neo4j_session, TENANT_ID, client, 1)
    await _sync_users(neo4j_session, TENANT_ID, client, 1)

    # Assert
    assert check_nodes(
        neo4j_session, "EntraDomain", ["id", "name", "authentication_type"]
    ) == {
        (f"{TENANT_ID}/contoso.com", "contoso.com", "Federated"),
        (
            f"{TENANT_ID}/contoso.onmicrosoft.com",
            "contoso.onmicrosoft.com",
            "Managed",
        ),
        (f"{OTHER_TENANT_ID}/contoso.com", "contoso.com", "Managed"),
    }
    assert check_rels(
        neo4j_session,
        "EntraDomain",
        "id",
        "AzureTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TENANT_ID}/contoso.com", TENANT_ID),
        (f"{TENANT_ID}/contoso.onmicrosoft.com", TENANT_ID),
        (f"{OTHER_TENANT_ID}/contoso.com", OTHER_TENANT_ID),
    }
    assert check_rels(
        neo4j_session, "EntraUser", "id", "EntraDomain", "id", "IN_DOMAIN"
    ) == {
        ("member", f"{TENANT_ID}/contoso.com"),
        ("guest", f"{TENANT_ID}/contoso.onmicrosoft.com"),
    }


@pytest.mark.asyncio  # type: ignore[misc]
async def test_removed_domain_is_cleaned_up_within_its_tenant(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    for tenant_id in (TENANT_ID, OTHER_TENANT_ID):
        load_tenant(neo4j_session, {"id": tenant_id}, 1)
        await _sync_domains(
            neo4j_session,
            tenant_id,
            _graph_client([Domain(id="contoso.com"), Domain(id="retired.contoso.com")]),
            1,
        )

    # Act
    await _sync_domains(
        neo4j_session, TENANT_ID, _graph_client([Domain(id="contoso.com")]), 2
    )

    # Assert
    assert check_nodes(neo4j_session, "EntraDomain", ["id"]) == {
        (f"{TENANT_ID}/contoso.com",),
        (f"{OTHER_TENANT_ID}/contoso.com",),
        (f"{OTHER_TENANT_ID}/retired.contoso.com",),
    }
