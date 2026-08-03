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

# The exposure the real get_exposure() would resolve from the domain fixtures:
# donut-photos is served on both its r2.dev domain and an enabled custom domain,
# nuclear-safety-reports on neither.
EXPOSURE = {
    "donut-photos": {
        "public": True,
        "public_domains": [
            "pub-3f8b1c2d4e5a6b7c8d9e0f1a2b3c4d5e.r2.dev",
            "photos.simpson.corp",
        ],
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


def _ensure_local_neo4j_has_test_r2buckets(neo4j_session):
    cartography.intel.cloudflare.r2buckets.load_r2buckets(
        neo4j_session,
        cartography.intel.cloudflare.r2buckets.transform_buckets(
            tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS,
            ACCOUNT_ID,
            EXPOSURE,
        ),
        ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


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


def test_get_returns_none_when_the_api_refuses_the_listing():
    """
    Ensure that an APIError on the bucket listing is swallowed so the Workers and
    ruleset stages still run
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
    def fake_managed_domain(client, account_id, bucket_name):
        return tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_MANAGED_DOMAINS[
            bucket_name
        ]

    def fake_custom_domains(client, account_id, bucket_name):
        return tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_CUSTOM_DOMAINS[bucket_name]

    # Act
    with (
        patch.object(
            cartography.intel.cloudflare.r2buckets,
            "get_managed_domain",
            side_effect=fake_managed_domain,
        ),
        patch.object(
            cartography.intel.cloudflare.r2buckets,
            "get_custom_domains",
            side_effect=fake_custom_domains,
        ),
    ):
        exposure = cartography.intel.cloudflare.r2buckets.get_exposure(
            None,
            tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS,
            ACCOUNT_ID,
        )

    # Assert: old-photos.simpson.corp is disabled and must not appear
    assert exposure == EXPOSURE


@patch.object(
    cartography.intel.cloudflare.r2buckets,
    "get_exposure",
    return_value=EXPOSURE,
)
@patch.object(
    cartography.intel.cloudflare.r2buckets,
    "get",
    return_value=tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_r2buckets(
    mock_cloudflare, mock_api, mock_exposure, neo4j_session
):
    """
    Ensure that R2 buckets actually get loaded with their internet exposure
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)

    # Act
    cartography.intel.cloudflare.r2buckets.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
    )

    # Assert buckets exist
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
