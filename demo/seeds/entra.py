from unittest.mock import AsyncMock
from unittest.mock import patch

import cartography.intel.entra.ou
import cartography.intel.entra.users
import tests.data.entra.ou
import tests.data.entra.users
from demo.seeds.base import AsyncSeed

TENANT_ID = tests.data.entra.users.TEST_TENANT_ID
CLIENT_ID = "fake-client-id"
CLIENT_SECRET = "fake-client-secret"


class EntraSeed(AsyncSeed):
    @patch.object(
        cartography.intel.entra.ou,
        "get_entra_ous",
        new_callable=AsyncMock,
        return_value=tests.data.entra.ou.MOCK_ENTRA_OUS,
    )
    @patch.object(
        cartography.intel.entra.users,
        "get_tenant",
        new_callable=AsyncMock,
        return_value=tests.data.entra.users.MOCK_ENTRA_TENANT,
    )
    @patch.object(
        cartography.intel.entra.users,
        "get_users",
        new_callable=AsyncMock,
        return_value=tests.data.entra.users.MOCK_ENTRA_USERS,
    )
    async def seed(self, *args) -> None:
        await self._seed_users()
        await self._seed_ous()

    async def _seed_users(self) -> None:
        await cartography.intel.entra.users.sync_entra_users(
            self.neo4j_session,
            TENANT_ID,
            CLIENT_ID,
            CLIENT_SECRET,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag, "TENANT_ID": TENANT_ID},
        )

    async def _seed_ous(self) -> None:
        await cartography.intel.entra.ou.sync_entra_ous(
            self.neo4j_session,
            TENANT_ID,
            CLIENT_ID,
            CLIENT_SECRET,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag, "TENANT_ID": TENANT_ID},
        )
