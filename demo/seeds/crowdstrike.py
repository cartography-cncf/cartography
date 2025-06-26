import cartography.intel.crowdstrike.endpoints
import cartography.intel.crowdstrike.spotlight
import tests.data.crowdstrike.endpoints
import tests.data.crowdstrike.spotlight
from demo.seeds.base import Seed


class CrowdsrikeSeed(Seed):
    def seed(self, *args) -> None:
        self._seed_hosts()
        self._seed_vulnerabilities()

    def _seed_hosts(self) -> None:
        cartography.intel.crowdstrike.endpoints.load_host_data(
            self.neo4j_session,
            tests.data.crowdstrike.endpoints.GET_HOSTS,
            self.update_tag,
        )

    def _seed_vulnerabilities(self) -> None:
        vulnerability_data = (
            tests.data.crowdstrike.spotlight.GET_SPOTLIGHT_VULNERABILITIES
        )
        cartography.intel.crowdstrike.spotlight.load_vulnerability_data(
            self.neo4j_session,
            vulnerability_data,
            self.update_tag,
        )
