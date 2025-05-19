import cartography.intel.snipeit.asset
import cartography.intel.snipeit.user
import tests.data.snipeit.assets
import tests.data.snipeit.tenants
import tests.data.snipeit.users
from demo.seeds.base import Seed


class SnipeitSeed(Seed):
    def seed(self, *args) -> None:
        for tenant_name, tenant in tests.data.snipeit.tenants.TENANTS.items():
            self._seed_users(tenant_name, tenant["id"])
            self._seed_assets(tenant_name, tenant["id"])

    def _seed_users(self, tenant_name: str, tenant_id: str) -> None:
        cartography.intel.snipeit.user.load_users(
            self.neo4j_session,
            {
                "UPDATE_TAG": self.update_tag,
                "TENANT_ID": tenant_id,
            },
            tests.data.snipeit.users.USERS[tenant_name],
        )

    def _seed_assets(self, tenant_name: str, tenant_id: str) -> None:
        cartography.intel.snipeit.asset.load_assets(
            self.neo4j_session,
            {
                "UPDATE_TAG": self.update_tag,
                "TENANT_ID": tenant_id,
            },
            tests.data.snipeit.assets.ASSETS[tenant_name],
        )
