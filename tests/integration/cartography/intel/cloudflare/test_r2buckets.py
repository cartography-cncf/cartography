from unittest.mock import patch

import cartography.intel.cloudflare.r2buckets
import tests.data.cloudflare.r2buckets
from tests.data.cloudflare.r2buckets_fakes import ACCOUNT_ID
from tests.data.cloudflare.r2buckets_fakes import DONUTS_DEFAULT
from tests.data.cloudflare.r2buckets_fakes import DONUTS_EU
from tests.data.cloudflare.r2buckets_fakes import fake_managed_domain
from tests.data.cloudflare.r2buckets_fakes import patch_domain_api
from tests.data.cloudflare.r2buckets_fakes import R2_DEV_DOMAIN
from tests.data.cloudflare.r2buckets_fakes import REPORTS_DEFAULT
from tests.data.cloudflare.r2buckets_fakes import ZONE_ID
from tests.integration.cartography.intel.cloudflare.test_accounts import (
    _ensure_local_neo4j_has_test_accounts,
)
from tests.integration.cartography.intel.cloudflare.test_zones import (
    _ensure_local_neo4j_has_test_zones,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789

# What get() returns when only the default jurisdiction could be listed.
DEFAULT_ONLY_BUCKETS = [
    bucket
    for bucket in tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS
    if bucket["jurisdiction"] == "default"
]


def _ensure_local_neo4j_has_test_r2buckets(neo4j_session):
    managed_patch, custom_patch = patch_domain_api()
    with managed_patch, custom_patch:
        exposure, _ = cartography.intel.cloudflare.r2buckets.get_exposure(
            None,
            tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS,
            ACCOUNT_ID,
        )
    cartography.intel.cloudflare.r2buckets.load_r2buckets(
        neo4j_session,
        cartography.intel.cloudflare.r2buckets.transform_buckets(
            tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS,
            ACCOUNT_ID,
            exposure,
        ),
        ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.cloudflare.r2buckets,
    "get",
    return_value=(tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS, True),
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_r2buckets(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that R2 buckets actually get loaded, with their internet exposure
    resolved by the real get_exposure() path
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)
    managed_patch, custom_patch = patch_domain_api()

    # Act
    with managed_patch, custom_patch:
        cartography.intel.cloudflare.r2buckets.sync(
            neo4j_session,
            mock_cloudflare,
            common_job_parameters,
            ACCOUNT_ID,
        )

    # Assert buckets exist. The default donut-photos is served on both its r2.dev
    # domain and an enabled custom domain; nuclear-safety-reports and the EU
    # donut-photos on neither. The two donut-photos buckets are distinct nodes.
    expected_nodes = {
        (DONUTS_DEFAULT, "donut-photos", "default", "wnam", True, True),
        (REPORTS_DEFAULT, "nuclear-safety-reports", "default", "enam", False, False),
        (DONUTS_EU, "donut-photos", "eu", "eeur", False, False),
    }
    assert (
        check_nodes(
            neo4j_session,
            "CloudflareR2Bucket",
            ["id", "name", "jurisdiction", "location", "public", "r2_dev_enabled"],
        )
        == expected_nodes
    )
    # exposed_internet is the cross-provider name for the same verdict.
    assert check_nodes(
        neo4j_session, "CloudflareR2Bucket", ["id", "exposed_internet"]
    ) == {
        (DONUTS_DEFAULT, True),
        (REPORTS_DEFAULT, False),
        (DONUTS_EU, False),
    }

    # Assert the public hostnames were resolved, and that the disabled custom
    # domain (old-photos.simpson.corp) was left out
    result = neo4j_session.run(
        """
        MATCH (b:CloudflareR2Bucket {id: $id})
        RETURN b.public_domains AS domains
        """,
        id=DONUTS_DEFAULT,
    )
    assert sorted(result.single()["domains"]) == [
        "photos.simpson.corp",
        R2_DEV_DOMAIN,
    ]

    # Assert buckets are connected with Account
    expected_rels = {
        (DONUTS_DEFAULT, ACCOUNT_ID),
        (REPORTS_DEFAULT, ACCOUNT_ID),
        (DONUTS_EU, ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareR2Bucket",
            "id",
            "CloudflareAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert only the bucket with an enabled custom domain is linked to its zone
    assert check_rels(
        neo4j_session,
        "CloudflareR2Bucket",
        "id",
        "CloudflareZone",
        "id",
        "HAS_R2_CUSTOM_DOMAIN",
        rel_direction_right=False,
    ) == {(DONUTS_DEFAULT, ZONE_ID)}

    # Assert the ObjectStorage ontology label and its normalized properties land
    result = neo4j_session.run(
        """
        MATCH (b:CloudflareR2Bucket:ObjectStorage)
        RETURN b.id AS id,
               b._ont_name AS name,
               b._ont_location AS location,
               b._ont_encrypted AS encrypted,
               b._ont_public AS public
        ORDER BY id
        """
    )
    assert [dict(record) for record in result] == [
        {
            "id": DONUTS_DEFAULT,
            "name": "donut-photos",
            "location": "wnam",
            "encrypted": True,
            "public": True,
        },
        {
            "id": REPORTS_DEFAULT,
            "name": "nuclear-safety-reports",
            "location": "enam",
            "encrypted": True,
            "public": False,
        },
        {
            "id": DONUTS_EU,
            "name": "donut-photos",
            "location": "eeur",
            "encrypted": True,
            "public": False,
        },
    ]


@patch.object(cartography.intel.cloudflare.r2buckets, "cleanup")
@patch.object(cartography.intel.cloudflare.r2buckets, "get", return_value=([], False))
@patch("cloudflare.Cloudflare")
def test_r2buckets_sync_skips_cleanup_when_listing_fails(
    mock_cloudflare, mock_api, mock_cleanup, neo4j_session
):
    """
    Ensure that a refused bucket listing skips the R2 stage without deleting the
    buckets ingested by earlier runs
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_r2buckets(neo4j_session)

    # Act
    cartography.intel.cloudflare.r2buckets.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
    )

    # Assert the previously ingested buckets survived
    mock_cleanup.assert_not_called()
    assert check_nodes(neo4j_session, "CloudflareR2Bucket", ["id"]) == {
        (DONUTS_DEFAULT,),
        (REPORTS_DEFAULT,),
        (DONUTS_EU,),
    }


@patch.object(cartography.intel.cloudflare.r2buckets, "cleanup")
@patch.object(
    cartography.intel.cloudflare.r2buckets,
    "get",
    return_value=(DEFAULT_ONLY_BUCKETS, False),
)
@patch("cloudflare.Cloudflare")
def test_r2buckets_sync_skips_cleanup_when_one_jurisdiction_is_unreadable(
    mock_cloudflare, mock_api, mock_cleanup, neo4j_session
):
    """
    Ensure that an unreadable jurisdiction holds the cleanup back: the buckets of
    the jurisdictions that were listed still ingest, but the ones this run knows
    nothing about must not be deleted
    """

    # Arrange: an earlier, complete run ingested every jurisdiction
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_r2buckets(neo4j_session)
    managed_patch, custom_patch = patch_domain_api()

    # Act: this run could only list the default jurisdiction
    with managed_patch, custom_patch:
        cartography.intel.cloudflare.r2buckets.sync(
            neo4j_session,
            mock_cloudflare,
            common_job_parameters,
            ACCOUNT_ID,
        )

    # Assert the EU bucket from the earlier run survived
    mock_cleanup.assert_not_called()
    assert check_nodes(neo4j_session, "CloudflareR2Bucket", ["id"]) == {
        (DONUTS_DEFAULT,),
        (REPORTS_DEFAULT,),
        (DONUTS_EU,),
    }


@patch.object(cartography.intel.cloudflare.r2buckets, "cleanup")
@patch.object(
    cartography.intel.cloudflare.r2buckets,
    "get_custom_domains",
    return_value=None,
)
@patch.object(
    cartography.intel.cloudflare.r2buckets,
    "get_managed_domain",
    side_effect=fake_managed_domain,
)
@patch.object(
    cartography.intel.cloudflare.r2buckets,
    "get",
    return_value=(tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS, True),
)
@patch("cloudflare.Cloudflare")
def test_r2buckets_sync_keeps_custom_domain_rels_on_partial_read(
    mock_cloudflare, mock_api, mock_managed, mock_custom, mock_cleanup, neo4j_session
):
    """
    Ensure that a refused custom-domain lookup does not delete the existing
    HAS_R2_CUSTOM_DOMAIN edges: the buckets still ingest, but cleanup is held back
    rather than treating the unknown domain set as an authoritative empty one
    """

    # Arrange: a previous run resolved donut-photos' custom domain
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)
    managed_patch, custom_patch = patch_domain_api()
    with managed_patch, custom_patch:
        cartography.intel.cloudflare.r2buckets.sync(
            neo4j_session,
            mock_cloudflare,
            common_job_parameters,
            ACCOUNT_ID,
        )
    # That first sync was complete, so it legitimately cleaned up; only the
    # partial run below must hold cleanup back.
    mock_cleanup.reset_mock()

    # Act: this run cannot read the custom domains
    cartography.intel.cloudflare.r2buckets.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
    )

    # Assert the zone relationship from the earlier run is still there
    mock_cleanup.assert_not_called()
    assert check_rels(
        neo4j_session,
        "CloudflareR2Bucket",
        "id",
        "CloudflareZone",
        "id",
        "HAS_R2_CUSTOM_DOMAIN",
        rel_direction_right=False,
    ) == {(DONUTS_DEFAULT, ZONE_ID)}

    # Assert the exposure is reported as unknown rather than private for the buckets where
    # nothing was seen, since the source that could not be read is the one holding the custom
    # domains. donut-photos is the exception: its r2.dev domain was read and is enabled, and a
    # domain that was actually seen makes the bucket readable whatever the other source did.
    result = neo4j_session.run(
        """
        MATCH (b:CloudflareR2Bucket)
        RETURN b.id AS id,
               b.public AS public,
               b.exposed_internet AS exposed,
               b.public_domains AS domains,
               b.r2_dev_enabled AS r2_dev
        ORDER BY id
        """
    )
    assert [dict(record) for record in result] == [
        {
            "id": DONUTS_DEFAULT,
            "public": True,
            "exposed": True,
            "domains": None,
            "r2_dev": True,
        },
        {
            "id": REPORTS_DEFAULT,
            "public": None,
            "exposed": None,
            "domains": None,
            "r2_dev": False,
        },
        {
            "id": DONUTS_EU,
            "public": None,
            "exposed": None,
            "domains": None,
            "r2_dev": False,
        },
    ]
