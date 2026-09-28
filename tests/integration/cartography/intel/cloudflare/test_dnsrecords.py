from unittest.mock import patch

import cartography.intel.cloudflare.dnsrecords
import tests.data.cloudflare.accounts
import tests.data.cloudflare.dnsrecords
import tests.data.cloudflare.zones
from tests.integration.cartography.intel.cloudflare.test_accounts import (
    _ensure_local_neo4j_has_test_accounts,
)
from tests.integration.cartography.intel.cloudflare.test_zones import (
    _ensure_local_neo4j_has_test_zones,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS[0]["id"]
ZONE_ID = tests.data.cloudflare.zones.CLOUDFLARE_ZONES[0]["id"]


@patch.object(
    cartography.intel.cloudflare.dnsrecords,
    "get",
    return_value=tests.data.cloudflare.dnsrecords.CLOUDFLARE_DNSRECORDS,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_dnsrecords(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that dnsrecords actually get loaded
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)

    # Act
    cartography.intel.cloudflare.dnsrecords.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
        tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
    )

    # Assert DNSRecords exist
    expected_nodes = {
        (
            "2b534a38-8658-48c0-8d6d-f9277d689c75",
            "simpson.corp",
            "A",
            "1.2.3.4",
        ),
        (
            "922f7919-e12b-4f46-800f-74b433724d29",
            "www.simpson.corp",
            "CNAME",
            "simpson.corp",
        ),
    }
    assert (
        check_nodes(
            neo4j_session, "CloudflareDNSRecord", ["id", "name", "type", "value"]
        )
        == expected_nodes
    )

    # Assert DNSRecords are connected with Account (the tenant)
    expected_account_rels = {
        ("2b534a38-8658-48c0-8d6d-f9277d689c75", ACCOUNT_ID),
        ("922f7919-e12b-4f46-800f-74b433724d29", ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareDNSRecord",
            "id",
            "CloudflareAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_account_rels
    )

    # Assert DNSRecords are connected with Zone
    expected_zone_rels = {
        ("2b534a38-8658-48c0-8d6d-f9277d689c75", ZONE_ID),
        ("922f7919-e12b-4f46-800f-74b433724d29", ZONE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareDNSRecord",
            "id",
            "CloudflareZone",
            "id",
            "HAS_RECORD",
            rel_direction_right=False,
        )
        == expected_zone_rels
    )

    # Assert the deprecated Zone RESOURCE edge is still created
    assert (
        check_rels(
            neo4j_session,
            "CloudflareDNSRecord",
            "id",
            "CloudflareZone",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_zone_rels
    )


def test_cloudflare_dnsrecord_resource_edge_migration_cleans_legacy_records(
    neo4j_session,
):
    """
    Ensure records ingested before the sub-resource moved from the zone to the
    account get the account RESOURCE edge backfilled, so the account-scoped
    cleanup can remove the ones the API no longer returns. Records whose zone was
    already deleted under the old per-zone scoping have no owner to backfill from
    and are swept instead.
    """
    # Arrange: a legacy record carrying only the zone RESOURCE edge, a current
    # one that the running sync just refreshed, and one orphaned by a zone that
    # was removed before the upgrade.
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)
    neo4j_session.run(
        """
        MATCH (z:CloudflareZone {id: $zone_id})
        MERGE (stale:CloudflareDNSRecord {id: 'legacy-stale'})
        SET stale.lastupdated = $old_update_tag
        MERGE (z)-[stale_rel:RESOURCE]->(stale)
        SET stale_rel.lastupdated = $old_update_tag
        MERGE (fresh:CloudflareDNSRecord {id: 'legacy-fresh'})
        SET fresh.lastupdated = $update_tag
        MERGE (z)-[fresh_rel:RESOURCE]->(fresh)
        SET fresh_rel.lastupdated = $update_tag
        MERGE (orphan:CloudflareDNSRecord {id: 'legacy-orphan'})
        SET orphan.lastupdated = $old_update_tag
        """,
        zone_id=ZONE_ID,
        old_update_tag=TEST_UPDATE_TAG - 1,
        update_tag=TEST_UPDATE_TAG,
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }

    # Act
    cartography.intel.cloudflare.dnsrecords.migrate_account_resource_edges(
        neo4j_session,
        common_job_parameters,
    )

    # Assert both zone-owned legacy records are now reachable from the account
    assert {
        ("legacy-stale", ACCOUNT_ID),
        ("legacy-fresh", ACCOUNT_ID),
    } <= check_rels(
        neo4j_session,
        "CloudflareDNSRecord",
        "id",
        "CloudflareAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    )

    # Assert the ownerless record was swept: no owner means no cleanup scope
    # could ever reach it, so the migration deletes it outright.
    swept = {
        record_id
        for (record_id,) in check_nodes(neo4j_session, "CloudflareDNSRecord", ["id"])
    }
    assert "legacy-orphan" not in swept

    # Act: the account-scoped cleanup can now see the backfilled records
    cartography.intel.cloudflare.dnsrecords.cleanup(
        neo4j_session, common_job_parameters
    )

    # Assert the stale record is gone and the refreshed one survives: the
    # backfilled edge carries the record's own lastupdated, so it does not
    # rescue records the API stopped returning.
    remaining = {
        record_id
        for (record_id,) in check_nodes(neo4j_session, "CloudflareDNSRecord", ["id"])
    }
    assert "legacy-stale" not in remaining
    assert "legacy-fresh" in remaining
