from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.devices
import cartography.intel.tailscale.postureintegrations
import cartography.intel.tailscale.tailnets
import cartography.intel.tailscale.users
import tests.data.tailscale.acls
import tests.data.tailscale.devices
import tests.data.tailscale.postureintegrations
import tests.data.tailscale.tailnets
import tests.data.tailscale.users
from demo.seeds.base import Seed

TAILSCALE_ORG = "simpson.corp"


class TailscaleSeed(Seed):
    @patch.object(
        cartography.intel.tailscale.users,
        "get",
        return_value=tests.data.tailscale.users.TAILSCALE_USERS,
    )
    @patch.object(
        cartography.intel.tailscale.tailnets,
        "get",
        return_value=tests.data.tailscale.tailnets.TAILSCALE_TAILNET,
    )
    @patch.object(
        cartography.intel.tailscale.acls,
        "get",
        return_value=tests.data.tailscale.acls.TAILSCALE_ACL_FILE,
    )
    @patch.object(
        cartography.intel.tailscale.devices,
        "get",
        return_value=tests.data.tailscale.devices.TAILSCALE_DEVICES,
    )
    @patch.object(
        cartography.intel.tailscale.postureintegrations,
        "get",
        return_value=tests.data.tailscale.postureintegrations.TAILSCALE_POSTUREINTEGRATIONS,
    )
    def seed(self, *args) -> None:
        mock_api = Mock()
        self._seed_tailnets(mock_api)
        users = self._seed_users(mock_api)
        self._seed_devices(mock_api)
        self._seed_posture_integrations(mock_api)
        self._seed_acls(mock_api, users)

    def _seed_tailnets(self, mock_api: Mock) -> None:
        cartography.intel.tailscale.tailnets.sync(
            self.neo4j_session,
            mock_api,
            {
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://fake.tailscale.com",
                "org": TAILSCALE_ORG,
            },
            org=TAILSCALE_ORG,
        )

    def _seed_users(self, mock_api: Mock) -> list[dict]:
        users = cartography.intel.tailscale.users.sync(
            self.neo4j_session,
            mock_api,
            {
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://fake.tailscale.com",
                "org": TAILSCALE_ORG,
            },
            org=TAILSCALE_ORG,
        )
        return users

    def _seed_devices(self, mock_api: Mock) -> None:
        cartography.intel.tailscale.devices.sync(
            self.neo4j_session,
            mock_api,
            {
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://fake.tailscale.com",
                "org": TAILSCALE_ORG,
            },
            org=TAILSCALE_ORG,
        )

    def _seed_posture_integrations(self, mock_api: Mock) -> None:
        cartography.intel.tailscale.postureintegrations.sync(
            self.neo4j_session,
            mock_api,
            {
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://fake.tailscale.com",
                "org": TAILSCALE_ORG,
            },
            org=TAILSCALE_ORG,
        )

    def _seed_acls(self, mock_api: Mock, users: list[dict]) -> None:
        cartography.intel.tailscale.acls.sync(
            self.neo4j_session,
            mock_api,
            {
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://fake.tailscale.com",
                "org": TAILSCALE_ORG,
            },
            org=TAILSCALE_ORG,
            users=users,
        )
