"""
Shared identifiers and API fakes for the Cloudflare R2 bucket tests, used by both
the unit and the integration suites.
"""

from unittest.mock import patch

import cartography.intel.cloudflare.r2buckets
import tests.data.cloudflare.accounts
import tests.data.cloudflare.r2buckets

ACCOUNT_ID = tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS[0]["id"]
ZONE_ID = "be68b067-5b2b-49f7-ad89-943d501dc900"
R2_DEV_DOMAIN = "pub-3f8b1c2d4e5a6b7c8d9e0f1a2b3c4d5e.r2.dev"

DONUTS_DEFAULT = f"{ACCOUNT_ID}/default/donut-photos"
DONUTS_EU = f"{ACCOUNT_ID}/eu/donut-photos"
REPORTS_DEFAULT = f"{ACCOUNT_ID}/default/nuclear-safety-reports"


def fake_managed_domain(client, account_id, bucket_name, jurisdiction):
    return tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_MANAGED_DOMAINS[
        (jurisdiction, bucket_name)
    ]


def fake_custom_domains(client, account_id, bucket_name, jurisdiction):
    return tests.data.cloudflare.r2buckets.CLOUDFLARE_R2_CUSTOM_DOMAINS[
        (jurisdiction, bucket_name)
    ]


def patch_domain_api():
    """
    Patch only the two API-facing domain fetches, so get_exposure() and
    transform_buckets() run for real.
    """
    return (
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
    )
