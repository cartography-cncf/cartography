from unittest.mock import MagicMock
from unittest.mock import patch

from cloudflare import APIError

import cartography.intel.cloudflare.r2buckets
import tests.data.cloudflare.accounts
import tests.data.cloudflare.r2buckets
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
ZONE_ID = "be68b067-5b2b-49f7-ad89-943d501dc900"
R2_DEV_DOMAIN = "pub-3f8b1c2d4e5a6b7c8d9e0f1a2b3c4d5e.r2.dev"


def _fake_managed_domain(client, account_id, bucket_name):
    return tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_MANAGED_DOMAINS[bucket_name]


def _fake_custom_domains(client, account_id, bucket_name):
    return tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_CUSTOM_DOMAINS[bucket_name]


def _patch_domain_api():
    """
    Patch only the two API-facing domain fetches, so get_exposure() and
    transform_buckets() run for real.
    """
    return (
        patch.object(
            cartography.intel.cloudflare.r2buckets,
            "get_managed_domain",
            side_effect=_fake_managed_domain,
        ),
        patch.object(
            cartography.intel.cloudflare.r2buckets,
            "get_custom_domains",
            side_effect=_fake_custom_domains,
        ),
    )


def _ensure_local_neo4j_has_test_r2buckets(neo4j_session):
    managed_patch, custom_patch = _patch_domain_api()
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
    return_value=tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS,
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
    managed_patch, custom_patch = _patch_domain_api()

    # Act
    with managed_patch, custom_patch:
        cartography.intel.cloudflare.r2buckets.sync(
            neo4j_session,
            mock_cloudflare,
            common_job_parameters,
            ACCOUNT_ID,
        )

    # Assert buckets exist. donut-photos is served on both its r2.dev domain and
    # an enabled custom domain; nuclear-safety-reports on neither.
    expected_nodes = {
        (f"{ACCOUNT_ID}/donut-photos", "donut-photos", "wnam", True, True),
        (
            f"{ACCOUNT_ID}/nuclear-safety-reports",
            "nuclear-safety-reports",
            "enam",
            False,
            False,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "CloudflareR2Bucket",
            ["id", "name", "location", "public", "r2_dev_enabled"],
        )
        == expected_nodes
    )

    # Assert the public hostnames were resolved, and that the disabled custom
    # domain (old-photos.simpson.corp) was left out
    result = neo4j_session.run(
        """
        MATCH (b:CloudflareR2Bucket {name: 'donut-photos'})
        RETURN b.public_domains AS domains
        """
    )
    assert sorted(result.single()["domains"]) == [
        "photos.simpson.corp",
        R2_DEV_DOMAIN,
    ]

    # Assert buckets are connected with Account
    expected_rels = {
        (f"{ACCOUNT_ID}/donut-photos", ACCOUNT_ID),
        (f"{ACCOUNT_ID}/nuclear-safety-reports", ACCOUNT_ID),
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
    ) == {(f"{ACCOUNT_ID}/donut-photos", ZONE_ID)}

    # Assert the ObjectStorage ontology label and its normalized properties land
    result = neo4j_session.run(
        """
        MATCH (b:CloudflareR2Bucket:ObjectStorage)
        RETURN b._ont_name AS name,
               b._ont_location AS location,
               b._ont_encrypted AS encrypted,
               b._ont_public AS public
        ORDER BY name
        """
    )
    assert [dict(record) for record in result] == [
        {
            "name": "donut-photos",
            "location": "wnam",
            "encrypted": True,
            "public": True,
        },
        {
            "name": "nuclear-safety-reports",
            "location": "enam",
            "encrypted": True,
            "public": False,
        },
    ]


@patch.object(cartography.intel.cloudflare.r2buckets, "cleanup")
@patch.object(cartography.intel.cloudflare.r2buckets, "get", return_value=None)
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
    assert check_nodes(neo4j_session, "CloudflareR2Bucket", ["name"]) == {
        ("donut-photos",),
        ("nuclear-safety-reports",),
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
    side_effect=_fake_managed_domain,
)
@patch.object(
    cartography.intel.cloudflare.r2buckets,
    "get",
    return_value=tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS,
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
    managed_patch, custom_patch = _patch_domain_api()
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
    ) == {(f"{ACCOUNT_ID}/donut-photos", ZONE_ID)}

    # Assert the exposure is reported as unknown rather than private: the source
    # that could not be read is the one holding the custom domains
    result = neo4j_session.run(
        """
        MATCH (b:CloudflareR2Bucket)
        RETURN b.name AS name,
               b.public AS public,
               b.public_domains AS domains,
               b.r2_dev_enabled AS r2_dev
        ORDER BY name
        """
    )
    assert [dict(record) for record in result] == [
        {"name": "donut-photos", "public": None, "domains": None, "r2_dev": True},
        {
            "name": "nuclear-safety-reports",
            "public": None,
            "domains": None,
            "r2_dev": False,
        },
    ]


def test_get_returns_none_when_the_api_refuses_the_listing():
    """
    Ensure that an APIError on the bucket listing is turned into None rather than
    propagating
    """

    # Arrange
    mock_client = MagicMock()
    mock_client.r2.buckets.list.side_effect = APIError(
        "Unauthorized", request=MagicMock(), body=None
    )

    # Act
    result = cartography.intel.cloudflare.r2buckets.get(mock_client, ACCOUNT_ID)

    # Assert
    assert result is None


def test_get_exposure_resolves_public_domains():
    """
    Ensure that the managed r2.dev domain and the custom domains are combined
    into the bucket exposure, ignoring the disabled ones
    """

    # Arrange
    managed_patch, custom_patch = _patch_domain_api()

    # Act
    with managed_patch, custom_patch:
        exposure, complete = cartography.intel.cloudflare.r2buckets.get_exposure(
            None,
            tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS,
            ACCOUNT_ID,
        )

    # Assert: old-photos.simpson.corp is disabled and must not appear
    assert complete is True
    assert exposure == {
        "donut-photos": {
            "public": True,
            "public_domains": [R2_DEV_DOMAIN, "photos.simpson.corp"],
            "r2_dev_enabled": True,
            "zone_ids": [ZONE_ID],
        },
        "nuclear-safety-reports": {
            "public": False,
            "public_domains": [],
            "r2_dev_enabled": False,
            "zone_ids": [],
        },
    }


def test_get_exposure_leaves_public_unknown_when_one_source_fails():
    """
    Ensure that a bucket is not reported as private when only one domain source
    could be read: the failed source can hold the only enabled domain
    """

    # Arrange: the r2.dev domain is disabled, but the custom domains are unknown
    buckets = [{"name": "donut-photos"}]

    # Act
    with (
        patch.object(
            cartography.intel.cloudflare.r2buckets,
            "get_managed_domain",
            return_value={"domain": R2_DEV_DOMAIN, "enabled": False},
        ),
        patch.object(
            cartography.intel.cloudflare.r2buckets,
            "get_custom_domains",
            return_value=None,
        ),
    ):
        exposure, complete = cartography.intel.cloudflare.r2buckets.get_exposure(
            None, buckets, ACCOUNT_ID
        )

    # Assert
    assert complete is False
    assert exposure["donut-photos"]["public"] is None
    assert exposure["donut-photos"]["public_domains"] is None
    # The managed domain was read, so its own state is still reported
    assert exposure["donut-photos"]["r2_dev_enabled"] is False
