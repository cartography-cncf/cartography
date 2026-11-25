from unittest.mock import patch

import cartography.intel.pylon
import cartography.intel.pylon.organization
import cartography.intel.pylon.roles
import cartography.intel.pylon.teams
import cartography.intel.pylon.users
import tests.data.pylon.organization
import tests.data.pylon.roles
import tests.data.pylon.teams
import tests.data.pylon.users
from cartography.config import Config
from demo.seeds.base import Seed


class PylonSeed(Seed):
    @patch.object(
        cartography.intel.pylon.teams,
        "get",
        return_value=tests.data.pylon.teams.PYLON_TEAMS,
    )
    @patch.object(
        cartography.intel.pylon.users,
        "get",
        return_value=tests.data.pylon.users.PYLON_USERS,
    )
    @patch.object(
        cartography.intel.pylon.roles,
        "get",
        return_value=tests.data.pylon.roles.PYLON_ROLES,
    )
    @patch.object(
        cartography.intel.pylon.organization,
        "get",
        return_value=tests.data.pylon.organization.PYLON_ME,
    )
    def seed(self, *args) -> None:
        cartography.intel.pylon.start_pylon_ingestion(
            self.neo4j_session,
            Config(
                neo4j_uri="bolt://localhost:7687",
                update_tag=self.update_tag,
                pylon_api_token="pylon_api_demo",
            ),
        )
