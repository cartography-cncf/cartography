import asyncio
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from kiota_abstractions.api_error import APIError

from cartography.intel.microsoft.entra.ou import get_entra_ous
from cartography.intel.microsoft.entra.users import get_users


async def _collect(items: AsyncIterator[Any]) -> list[Any]:
    return [item async for item in items]


def _forbidden_error() -> APIError:
    error = APIError("forbidden")
    error.response_status_code = 403
    return error


def test_users_propagates_denial_from_later_page() -> None:
    # Arrange
    client = MagicMock()
    first_page = MagicMock(value=[MagicMock()], odata_next_link="next-page")
    client.users.get = AsyncMock(return_value=first_page)
    client.users.with_url.return_value.get = AsyncMock(side_effect=_forbidden_error())

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(_collect(get_users(client)))


def test_administrative_units_propagates_denial() -> None:
    # Arrange
    client = MagicMock()
    client.directory.administrative_units.get = AsyncMock(
        side_effect=_forbidden_error(),
    )

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(_collect(get_entra_ous(client)))
