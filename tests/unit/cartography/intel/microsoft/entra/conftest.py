from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest


@pytest.fixture  # type: ignore[misc]
def graph_client_class() -> MagicMock:
    """A GraphServiceClient stand-in whose optional Entra reports are empty."""
    client = MagicMock()
    client.reports.authentication_methods.user_registration_details.get = AsyncMock(
        return_value=None
    )
    client.identity_protection.risky_users.get = AsyncMock(return_value=None)
    client.identity_protection.risky_service_principals.get = AsyncMock(
        return_value=None
    )
    return MagicMock(return_value=client)
