from unittest.mock import patch

import digitalocean

import cartography.intel.digitalocean.compute
import cartography.intel.digitalocean.management
import tests.data.digitalocean.compute
import tests.data.digitalocean.management
import tests.data.digitalocean.platform
from demo.seeds.base import Seed

ACCOUNT_ID = tests.data.digitalocean.platform.ACCOUNT_RESPONSE.uuid
DROPLET_ID = tests.data.digitalocean.compute.DROPLETS_RESPONSE[0].id
PROJECT_ID = tests.data.digitalocean.management.PROJECTS_RESPONSE[0].id


class DigitalOceanSeed(Seed):
    @patch.object(
        cartography.intel.digitalocean.compute,
        "get_droplets",
        return_value=tests.data.digitalocean.compute.DROPLETS_RESPONSE,
    )
    @patch.object(
        cartography.intel.digitalocean.management,
        "get_projects",
        return_value=tests.data.digitalocean.management.PROJECTS_RESPONSE,
    )
    @patch.object(
        digitalocean.Project,
        "get_all_resources",
        return_value=tests.data.digitalocean.management.PROJECT_RESOURCES_RESPONSE,
    )
    @patch.object(
        cartography.intel.digitalocean.platform,
        "get_account",
        return_value=tests.data.digitalocean.platform.ACCOUNT_RESPONSE,
    )
    @patch("digitalocean.Manager")
    def seed(self, mock_do_manager, *args) -> None:
        self._seed_platform(mock_do_manager)
        self._seed_management(mock_do_manager)
        self._seed_compute(mock_do_manager)

    def _seed_platform(self, mock_do_manager) -> None:
        cartography.intel.digitalocean.platform.sync(
            self.neo4j_session,
            mock_do_manager,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag},
        )

    def _seed_management(self, mock_do_manager) -> None:
        cartography.intel.digitalocean.management.sync(
            self.neo4j_session,
            mock_do_manager,
            ACCOUNT_ID,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag, "ACCOUNT_ID": ACCOUNT_ID},
        )

    def _seed_compute(self, mock_do_manager) -> None:
        cartography.intel.digitalocean.compute.sync(
            self.neo4j_session,
            mock_do_manager,
            ACCOUNT_ID,
            {
                str(PROJECT_ID): [
                    "do:droplet:" + DROPLET_ID,
                ],
            },
            self.update_tag,
            {
                "UPDATE_TAG": self.update_tag,
                "ACCOUNT_ID": ACCOUNT_ID,
            },
        )
