from unittest.mock import patch

import cartography.intel.lastpass.users
import tests.data.lastpass.users
from demo.seeds.base import Seed

TENANT_ID = 11223344


class LastpassSeed(Seed):
    @patch.object(
        cartography.intel.lastpass.users,
        "get",
        return_value=tests.data.lastpass.users.LASTPASS_USERS,
    )
    def seed(self, *args) -> None:
        self._seed_users()

    def _seed_users(self) -> None:
        cartography.intel.lastpass.users.sync(
            self.neo4j_session,
            "fakeProvHash",
            TENANT_ID,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag, "TENANT_ID": TENANT_ID},
        )
