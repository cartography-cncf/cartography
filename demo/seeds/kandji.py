import cartography.intel.kandji.devices
import tests.data.kandji.devices
import tests.data.kandji.tenant
from demo.seeds.base import Seed


class KandjiSeed(Seed):
    def seed(self, *args) -> None:
        self._seed_devices()

    def _seed_devices(self) -> None:
        for tenant, tenant_data in tests.data.kandji.tenant.TENANT.items():

            cartography.intel.kandji.devices.load_devices(
                self.neo4j_session,
                {
                    "UPDATE_TAG": self.update_tag,
                    "TENANT_ID": tenant_data["id"],
                },
                tests.data.kandji.devices.DEVICES[f"{tenant}_devices"],
            )
