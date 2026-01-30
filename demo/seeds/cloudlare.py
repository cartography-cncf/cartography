from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.cloudflare.accounts
import cartography.intel.cloudflare.dnsrecords
import cartography.intel.cloudflare.members
import cartography.intel.cloudflare.roles
import cartography.intel.cloudflare.zones
import tests.data.cloudflare.accounts
import tests.data.cloudflare.dnsrecords
import tests.data.cloudflare.members
import tests.data.cloudflare.roles
import tests.data.cloudflare.zones
from demo.seeds.base import Seed


class CloudflareSeed(Seed):
    @patch.object(
        cartography.intel.cloudflare.accounts,
        "get",
        return_value=tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS,
    )
    @patch.object(
        cartography.intel.cloudflare.members,
        "get",
        return_value=tests.data.cloudflare.members.CLOUDFLARE_MEMBERS,
    )
    @patch.object(
        cartography.intel.cloudflare.roles,
        "get",
        return_value=tests.data.cloudflare.roles.CLOUDFLARE_ROLES,
    )
    @patch.object(
        cartography.intel.cloudflare.zones,
        "get",
        return_value=tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
    )
    @patch.object(
        cartography.intel.cloudflare.dnsrecords,
        "get",
        return_value=tests.data.cloudflare.dnsrecords.CLOUDFLARE_DNSRECORDS,
    )
    def seed(self, *args) -> None:
        mock_client = Mock()
        for account in self._seed_accounts(mock_client):
            self._seed_roles(mock_client, account)
            self._seed_members(mock_client, account)
            for zone in self._seed_zones(mock_client, account):
                self._seed_dns_records(mock_client, zone)

    def _seed_accounts(self, mock_client: Mock) -> list[dict]:
        return cartography.intel.cloudflare.accounts.sync(
            self.neo4j_session,
            mock_client,
            {
                "UPDATE_TAG": self.update_tag,
            },
        )

    def _seed_roles(self, mock_client: Mock, account: dict) -> None:
        cartography.intel.cloudflare.roles.sync(
            self.neo4j_session,
            mock_client,
            {
                "UPDATE_TAG": self.update_tag,
                "account_id": account["id"],
            },
            account_id=account["id"],
        )

    def _seed_members(self, mock_client: Mock, account: dict) -> None:
        cartography.intel.cloudflare.members.sync(
            self.neo4j_session,
            mock_client,
            {
                "UPDATE_TAG": self.update_tag,
                "account_id": account["id"],
            },
            account_id=account["id"],
        )

    def _seed_zones(self, mock_client: Mock, account: dict) -> list[dict]:
        return cartography.intel.cloudflare.zones.sync(
            self.neo4j_session,
            mock_client,
            {
                "UPDATE_TAG": self.update_tag,
                "account_id": account["id"],
            },
            account_id=account["id"],
        )

    def _seed_dns_records(self, mock_client: Mock, zone: dict) -> None:
        cartography.intel.cloudflare.dnsrecords.sync(
            self.neo4j_session,
            mock_client,
            {
                "UPDATE_TAG": self.update_tag,
                "zone_id": zone["id"],
            },
            zone_id=zone["id"],
        )
