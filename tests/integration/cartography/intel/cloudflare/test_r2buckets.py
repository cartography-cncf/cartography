from unittest.mock import MagicMock
from unittest.mock import patch

from cloudflare import APIError
from cloudflare import NotFoundError
from cloudflare import PermissionDeniedError

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

DONUTS_DEFAULT = f"{ACCOUNT_ID}/default/donut-photos"
DONUTS_EU = f"{ACCOUNT_ID}/eu/donut-photos"
REPORTS_DEFAULT = f"{ACCOUNT_ID}/default/nuclear-safety-reports"

# What get() returns when only the default jurisdiction could be listed.
DEFAULT_ONLY_BUCKETS = [
    bucket
    for bucket in tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS
    if bucket["jurisdiction"] == "default"
]


def _fake_managed_domain(client, account_id, bucket_name, jurisdiction):
    return tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_MANAGED_DOMAINS[
        (jurisdiction, bucket_name)
    ]


def _fake_custom_domains(client, account_id, bucket_name, jurisdiction):
    return tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_CUSTOM_DOMAINS[
        (jurisdiction, bucket_name)
    ]


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


def _mock_client_listing_every_jurisdiction(failures=None):
    """
    Build a Cloudflare client mock whose bucket listing answers per jurisdiction,
    raising for the jurisdictions named in `failures`.
    """
    failures = failures or {}

    def _list(account_id, per_page, jurisdiction, **kwargs):
        if jurisdiction in failures:
            raise failures[jurisdiction]
        page = MagicMock()
        page.buckets = [
            MagicMock(to_dict=MagicMock(return_value=dict(bucket)))
            for bucket in tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_BUCKETS_BY_JURISDICTION[
                jurisdiction
            ]
        ]
        return page

    mock_client = MagicMock()
    mock_client.r2.buckets.list.side_effect = _list
    return mock_client


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
    managed_patch, custom_patch = _patch_domain_api()

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
    managed_patch, custom_patch = _patch_domain_api()

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
    side_effect=_fake_managed_domain,
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


def test_get_lists_every_jurisdiction():
    """
    Ensure that every R2 jurisdiction is listed and that each bucket carries the
    jurisdiction it was listed in: one listing only reports one jurisdiction, and
    the API omits the field on the default one
    """

    # Arrange
    mock_client = _mock_client_listing_every_jurisdiction()

    # Act
    buckets, complete = cartography.intel.cloudflare.r2buckets.get(
        mock_client, ACCOUNT_ID
    )

    # Assert
    assert complete is True
    assert [
        call.kwargs["jurisdiction"]
        for call in mock_client.r2.buckets.list.call_args_list
    ] == ["default", "eu", "fedramp"]
    assert {(bucket["jurisdiction"], bucket["name"]) for bucket in buckets} == {
        ("default", "donut-photos"),
        ("default", "nuclear-safety-reports"),
        ("eu", "donut-photos"),
    }


def test_get_treats_an_ungranted_jurisdiction_as_empty():
    """
    Ensure that a jurisdiction the account was never granted is reported as
    holding no bucket rather than as a failed read: it is granted on request, so
    treating it as a failure would hold back the cleanup of every other account
    """

    # Arrange
    mock_client = _mock_client_listing_every_jurisdiction(
        failures={
            "fedramp": NotFoundError("Not found", response=MagicMock(), body=None),
        }
    )

    # Act
    buckets, complete = cartography.intel.cloudflare.r2buckets.get(
        mock_client, ACCOUNT_ID
    )

    # Assert
    assert complete is True
    assert len(buckets) == 3


def test_get_reports_an_unreadable_jurisdiction_as_incomplete():
    """
    Ensure that an unexpected error on a jurisdiction listing is reported as a
    partial read, so the caller holds the cleanup back
    """

    # Arrange
    mock_client = _mock_client_listing_every_jurisdiction(
        failures={
            "eu": APIError("Server error", request=MagicMock(), body=None),
        }
    )

    # Act
    buckets, complete = cartography.intel.cloudflare.r2buckets.get(
        mock_client, ACCOUNT_ID
    )

    # Assert: the default jurisdiction still came through
    assert complete is False
    assert {bucket["jurisdiction"] for bucket in buckets} == {"default"}


def test_get_reports_no_buckets_when_the_default_listing_is_refused():
    """
    Ensure that a token without the R2 scope yields no bucket and a partial read,
    so the R2 stage is skipped instead of deleting the whole inventory
    """

    # Arrange: the default jurisdiction exists for every R2 account, so a refusal
    # there is a permission problem rather than a missing grant
    refusal = PermissionDeniedError("Forbidden", response=MagicMock(), body=None)
    mock_client = _mock_client_listing_every_jurisdiction(
        failures={
            jurisdiction: refusal for jurisdiction in ("default", "eu", "fedramp")
        }
    )

    # Act
    buckets, complete = cartography.intel.cloudflare.r2buckets.get(
        mock_client, ACCOUNT_ID
    )

    # Assert
    assert buckets == []
    assert complete is False


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

    # Assert: old-photos.simpson.corp is disabled and must not appear, and the two
    # same-named buckets are keyed apart by their jurisdiction
    assert complete is True
    assert exposure == {
        DONUTS_DEFAULT: {
            "public": True,
            "exposed_internet": True,
            "exposed_internet_type": ["direct"],
            "public_domains": [R2_DEV_DOMAIN, "photos.simpson.corp"],
            "r2_dev_enabled": True,
            "zone_ids": [ZONE_ID],
        },
        REPORTS_DEFAULT: {
            "public": False,
            "exposed_internet": False,
            "exposed_internet_type": None,
            "public_domains": [],
            "r2_dev_enabled": False,
            "zone_ids": [],
        },
        DONUTS_EU: {
            "public": False,
            "exposed_internet": False,
            "exposed_internet_type": None,
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
    buckets = [{"name": "donut-photos", "jurisdiction": "default"}]

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
    assert exposure[DONUTS_DEFAULT]["public"] is None
    assert exposure[DONUTS_DEFAULT]["public_domains"] is None
    # The managed domain was read, so its own state is still reported
    assert exposure[DONUTS_DEFAULT]["r2_dev_enabled"] is False


def test_get_exposure_reports_public_when_one_source_finds_a_domain():
    """
    A domain that was actually seen makes the bucket readable, whatever the other
    source did: gating that on a complete read hid live exposure
    """

    # Arrange: r2.dev is enabled, but the custom domains could not be read
    buckets = [{"name": "donut-photos", "jurisdiction": "default"}]

    # Act
    with (
        patch.object(
            cartography.intel.cloudflare.r2buckets,
            "get_managed_domain",
            return_value={"domain": R2_DEV_DOMAIN, "enabled": True},
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

    # Assert: the read is still incomplete, but the verdict is definitive
    assert complete is False
    assert exposure[DONUTS_DEFAULT]["public"] is True
    assert exposure[DONUTS_DEFAULT]["exposed_internet"] is True
    assert exposure[DONUTS_DEFAULT]["exposed_internet_type"] == ["direct"]
    # The hostname list stays unknown: it is the one field a partial read truncates
    assert exposure[DONUTS_DEFAULT]["public_domains"] is None
