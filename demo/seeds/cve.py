import cartography.intel.cve.feed
import tests.data.cve.feed
from demo.seeds.base import Seed


class CVESeed(Seed):
    def seed(self, *args) -> None:
        feed_metadata = self._seed_feeds()
        self._seed_cves(feed_metadata)

    def _seed_feeds(self) -> dict[str, str]:
        feed_metadata = cartography.intel.cve.feed.transform_cve_feed(
            tests.data.cve.feed.GET_CVE_API_DATA
        )
        cartography.intel.cve.feed.load_cve_feed(
            self.neo4j_session,
            [feed_metadata],
            self.update_tag,
        )
        return feed_metadata

    def _seed_cves(self, feed_metadata: dict[str, str]) -> None:
        published_cves = cartography.intel.cve.feed.transform_cves(
            tests.data.cve.feed.GET_CVE_API_DATA
        )
        cartography.intel.cve.feed.load_cves(
            self.neo4j_session,
            published_cves,
            feed_metadata["FEED_ID"],
            self.update_tag,
        )
