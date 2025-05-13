from unittest import TestCase
from unittest.mock import patch

import neo4j

import cartography.intel.lastpass.users
import tests.data.lastpass.users

TEST_TENANT_ID = 11223344


class LastpassSeed(TestCase):
    def __init__(self, neo4j_session: neo4j.Session, update_tag: int):
        super().__init__("seed")
        self.neo4j_session = neo4j_session
        self.update_tag = update_tag

    @patch.object(
        cartography.intel.lastpass.users,
        "get",
        return_value=tests.data.lastpass.users.LASTPASS_USERS,
    )
    def seed(self, mock_users) -> None:
        # DOC
        self._seed_users()

    def _seed_users(self) -> None:
        cartography.intel.lastpass.users.sync(
            self.neo4j_session,
            "fakeProvHash",
            TEST_TENANT_ID,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag, "TENANT_ID": TEST_TENANT_ID},
        )
