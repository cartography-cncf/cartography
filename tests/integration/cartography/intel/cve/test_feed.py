from cartography.intel.cve import feed
from tests.data.cve.feed import GET_CVE_API_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
NIST_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0/"
API_KEY = "nvd_api_key"


def _create_spotlight_nodes(neo4j_session):
    neo4j_session.run(
        """
        MERGE (v:SpotlightVulnerability{id: $spotlight_id})
        ON CREATE SET v.firstseen = timestamp()
        """,
        spotlight_id="CVE-2023-41782",
    )


def _create_sync_metadata(neo4j_session):
    neo4j_session.run(
        """
        MERGE (s:SyncMetadata{id: $id})
        ON CREATE SET s.firstseen = timestamp(),
            s.grouptype = $grouptype,
            s.syncedtype = "year",
            s.groupid = $groupid
        """,
        id="CVE_2023",
        grouptype="CVE",
        groupid="2023",
    )


def _create_cve_nodes(neo4j_session):
    neo4j_session.run(
        """
        MERGE (c:CVE{id: $cve_id})
        ON CREATE SET c.firstseen = timestamp(),
        c.lastupdated = $update_tag,
        c.published_date = $published_date,
        c.last_modified_date = $last_modified_date
        MERGE(feed:CVEFeed{id: $feed_id})-[:RESOURCE]->(c)
        """,
        cve_id="CVE-2023-9999",
        update_tag=TEST_UPDATE_TAG,
        published_date="2023-01-10T19:30:07.000",
        last_modified_date="2023-01-10T19:30:07.000",
        feed_id=feed.CVE_FEED_ID,
    )


def test_get_cve_sync_metadata(neo4j_session):
    # Arrange
    _create_sync_metadata(neo4j_session)

    # Act
    sync_metadata = feed.get_cve_sync_metadata(neo4j_session)

    # Assert
    assert sync_metadata == [2023]


def test_get_last_modified_cve_date(neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session)

    # Act
    last_modified_date = feed.get_last_modified_cve_date(neo4j_session)

    # Assert
    assert last_modified_date == "2023-01-10T19:30:07"


def test_sync(neo4j_session):
    # Arrange
    _create_spotlight_nodes(neo4j_session)
    _create_cve_nodes(neo4j_session)
    expected_feed = {(
        feed.CVE_FEED_ID,
        "NVD_CVE",
        "2.0",
        GET_CVE_API_DATA["timestamp"],
    )}
    expected_cves = {
        (cve["cve"]["id"], cve["cve"]["published"], cve["cve"]["lastModified"])
        for cve in GET_CVE_API_DATA.get("vulnerabilities")
    }
    expected_cves.add(("CVE-2023-9999", "2023-01-10T19:30:07.000", "2023-01-10T19:30:07.000"))
    expected_feed_cve_rels = {(feed.CVE_FEED_ID, cve_id[0]) for cve_id in expected_cves}
    # Act
    cves = GET_CVE_API_DATA
    feed_metadata = feed.transform_cve_feed(cves)
    feed.load_cve_feed(neo4j_session, [feed_metadata], TEST_UPDATE_TAG)
    published_cves = feed.transform_cves(cves)
    feed.load_cves(
        neo4j_session, published_cves, feed_metadata["FEED_ID"], TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session, "CVEFeed", ["id", "format", "version", "timestamp"],
    ) == expected_feed

    assert (
        check_nodes(
            neo4j_session, "CVE", ["id", "published_date", "last_modified_date"],
        ) ==
        expected_cves
    )

    assert (
        check_rels(neo4j_session, "CVEFeed", "id", "CVE", "id", "RESOURCE") ==
        expected_feed_cve_rels
    )

    assert check_rels(
        neo4j_session, "SpotlightVulnerability", "id", "CVE", "id", "HAS_CVE",
    ) == {
        ("CVE-2023-41782", "CVE-2023-41782"),
    }
