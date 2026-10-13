from unittest.mock import MagicMock
from unittest.mock import patch

from cloudflare import APIError
from cloudflare import NotFoundError
from cloudflare import PermissionDeniedError

import cartography.intel.cloudflare.r2buckets
import tests.data.cloudflare.r2buckets
from tests.data.cloudflare.r2buckets_fakes import ACCOUNT_ID
from tests.data.cloudflare.r2buckets_fakes import DONUTS_DEFAULT
from tests.data.cloudflare.r2buckets_fakes import DONUTS_EU
from tests.data.cloudflare.r2buckets_fakes import patch_domain_api
from tests.data.cloudflare.r2buckets_fakes import R2_DEV_DOMAIN
from tests.data.cloudflare.r2buckets_fakes import REPORTS_DEFAULT
from tests.data.cloudflare.r2buckets_fakes import ZONE_ID


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
    managed_patch, custom_patch = patch_domain_api()

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
