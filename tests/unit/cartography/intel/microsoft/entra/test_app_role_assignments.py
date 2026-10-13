import logging
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from kiota_abstractions.api_error import APIError

from cartography.intel.microsoft.entra.app_role_assignments import (
    get_app_role_assignments_for_app,
)


def _make_client_raising(exc: Exception) -> MagicMock:
    """
    Build a GraphServiceClient mock whose
    `service_principals.by_service_principal_id(...).app_role_assigned_to.get(...)`
    raises `exc`.
    """
    client = MagicMock()
    sp_builder = client.service_principals.by_service_principal_id.return_value
    sp_builder.app_role_assigned_to.get = AsyncMock(side_effect=exc)
    return client


def _make_neo4j_session_returning_sp(service_principal_id: str) -> MagicMock:
    session = MagicMock()
    session.execute_read.return_value = service_principal_id
    return session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, message, sp_id, app_id",
    [
        pytest.param(404, "not found", "sp-1", "app-1", id="not_found"),
        pytest.param(410, "gone", "sp-2", "app-2", id="gone"),
    ],
)
async def test_get_app_role_assignments_skips_deleted_sp(
    caplog, status, message, sp_id, app_id
):
    """
    A 404 (or 410 Gone) from Microsoft Graph when fetching appRoleAssignedTo for
    a service principal that was deleted between list and fetch should be logged
    and skipped, not re-raised. Otherwise a single deleted SP aborts the entire
    Entra sync.
    """
    # Arrange
    err = APIError(message)
    err.response_status_code = status
    client = _make_client_raising(err)
    neo4j_session = _make_neo4j_session_returning_sp(sp_id)

    # Act
    with caplog.at_level(logging.WARNING):
        results = [
            x
            async for x in get_app_role_assignments_for_app(
                client, neo4j_session, "tenant-1", app_id
            )
        ]

    # Assert
    assert results == []
    assert sp_id in caplog.text
    assert app_id in caplog.text


@pytest.mark.asyncio
async def test_get_app_role_assignments_reraises_other_apierrors():
    """Non-404/410 APIErrors (e.g. 403) must still propagate."""
    err = APIError("forbidden")
    err.response_status_code = 403
    client = _make_client_raising(err)
    neo4j_session = _make_neo4j_session_returning_sp("sp-3")

    with pytest.raises(APIError):
        async for _ in get_app_role_assignments_for_app(
            client, neo4j_session, "tenant-1", "app-3"
        ):
            pass
