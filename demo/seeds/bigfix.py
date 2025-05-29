from unittest.mock import patch

import cartography.intel.bigfix.computers
import tests.data.bigfix.computers
from demo.seeds.base import Seed

BIGFIX_ROOT_URL = "https://bigfixroot.example.com"
BIGFIX_USER = "myuser"
BIGFIX_PASSWORD = "mypassword"


class BigfixSeed(Seed):
    @patch.object(
        cartography.intel.bigfix.computers,
        "_get_computer_details_raw_xml",
        side_effect=tests.data.bigfix.computers.BF_COMPUTER_DETAILS,
    )
    @patch.object(
        cartography.intel.bigfix.computers,
        "_get_computer_list_raw_xml",
        return_value=tests.data.bigfix.computers.BF_COMPUTER_LIST,
    )
    def seed(self, *args) -> None:
        self._seed_computers()

    def _seed_computers(self) -> None:
        cartography.intel.bigfix.computers.sync(
            self.neo4j_session,
            BIGFIX_ROOT_URL,
            BIGFIX_USER,
            BIGFIX_PASSWORD,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag, "ROOT_URL": BIGFIX_ROOT_URL},
        )
