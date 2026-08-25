from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.digitalocean.compute
import cartography.intel.digitalocean.management
import tests.data.digitalocean.compute
import tests.data.digitalocean.management
import tests.data.digitalocean.platform
from demo.seeds.base import Seed

ACCOUNT_ID = tests.data.digitalocean.platform.ACCOUNT_RESPONSE["account"]["uuid"]
DROPLET_ID = tests.data.digitalocean.compute.DROPLETS_RESPONSE["droplets"][0]["id"]
PROJECT_ID = tests.data.digitalocean.management.PROJECTS_RESPONSE["projects"][0]["id"]


class DigitalOceanSeed(Seed):
    @patch.object(
        cartography.intel.digitalocean.compute,
        "get_droplets",
        return_value=tests.data.digitalocean.compute.DROPLETS_RESPONSE["droplets"],
    )
    @patch.object(
        cartography.intel.digitalocean.management,
        "get_projects",
        return_value=tests.data.digitalocean.management.PROJECTS_RESPONSE["projects"],
    )
    @patch.object(
        cartography.intel.digitalocean.platform,
        "get_account",
        return_value=tests.data.digitalocean.platform.ACCOUNT_RESPONSE["account"],
    )
    def seed(self, *args) -> None:
        mock_client = MagicMock()
        mock_client.projects.list_resources.return_value = (
            tests.data.digitalocean.management.PROJECT_RESOURCES_RESPONSE
        )
        self._seed_platform(mock_client)
        self._seed_management(mock_client)
        self._seed_compute(mock_client)

    def _seed_platform(self, mock_client) -> None:
        cartography.intel.digitalocean.platform.sync(
            self.neo4j_session,
            mock_client,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag},
        )

    def _seed_management(self, mock_client) -> None:
        cartography.intel.digitalocean.management.sync(
            self.neo4j_session,
            mock_client,
            ACCOUNT_ID,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag, "ACCOUNT_ID": ACCOUNT_ID},
        )

    def _seed_compute(self, mock_client) -> None:
        cartography.intel.digitalocean.compute.sync(
            self.neo4j_session,
            mock_client,
            ACCOUNT_ID,
            {
                str(PROJECT_ID): [
                    {
                        "urn": "do:droplet:" + str(DROPLET_ID),
                    }
                ],
            },
            self.update_tag,
            {
                "UPDATE_TAG": self.update_tag,
                "ACCOUNT_ID": ACCOUNT_ID,
            },
        )
