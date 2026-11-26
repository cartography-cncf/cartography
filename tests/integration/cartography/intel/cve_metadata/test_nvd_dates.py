from datetime import datetime
from datetime import timezone

from cartography.intel.cve_metadata import CVE_METADATA_FEED_ID
from cartography.intel.cve_metadata import load_cve_metadata
from cartography.intel.cve_metadata import load_cve_metadata_feed
from cartography.intel.cve_metadata.nvd import transform_cves
from tests.integration.util import check_rels


def test_nvd_resync_makes_existing_dates_queryable_as_utc(neo4j_session):
    # Arrange: this split-ingestion test targets upgrading stored temporal types.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cve_id = "CVE-2024-0001"
    neo4j_session.run("CREATE (:CVE {id: $id, cve_id: $id})", id=cve_id)
    load_cve_metadata_feed(neo4j_session, 1, {"nvd"})
    naive_date = datetime(2024, 1, 5, 2, 15, 7, 147000)
    load_cve_metadata(
        neo4j_session,
        [{"id": cve_id, "published": naive_date, "lastModified": naive_date}],
        1,
    )
    response = {
        "vulnerabilities": [
            {
                "cve": {
                    "id": cve_id,
                    "published": "2024-01-05T02:15:07.147",
                    "lastModified": "2024-01-05T02:15:07.147",
                },
            },
        ],
    }

    # Act: the ordinary transform/load path must correct existing values.
    transformed = transform_cves(response, {cve_id})
    load_cve_metadata(neo4j_session, list(transformed.values()), 2)

    # Assert: both properties now match an interval expressed as zoned datetimes.
    records = list(
        neo4j_session.run(
            "MATCH (m:CVEMetadata {id: $id}) "
            "WHERE m.published_date >= datetime('2024-01-01T00:00:00Z') "
            "AND m.published_date < datetime('2024-02-01T00:00:00Z') "
            "AND m.last_modified_date >= datetime('2024-01-01T00:00:00Z') "
            "AND m.last_modified_date < datetime('2024-02-01T00:00:00Z') "
            "RETURN m.published_date AS published, "
            "m.last_modified_date AS modified, m.lastupdated AS update_tag",
            id=cve_id,
        )
    )
    assert len(records) == 1
    expected = naive_date.replace(tzinfo=timezone.utc)
    assert records[0]["published"].to_native() == expected
    assert records[0]["modified"].to_native() == expected
    assert records[0]["update_tag"] == 2
    assert check_rels(
        neo4j_session, "CVEMetadata", "id", "CVE", "cve_id", "ENRICHES"
    ) == {(cve_id, cve_id)}
    assert check_rels(
        neo4j_session, "CVEMetadataFeed", "id", "CVEMetadata", "id", "RESOURCE"
    ) == {(CVE_METADATA_FEED_ID, cve_id)}
