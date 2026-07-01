from cartography.intel.tenable.common import get_tenant_id_from_url
from cartography.intel.tenable.common import make_tenable_id


def test_get_tenant_id_from_url_uses_hostname_only():
    assert get_tenant_id_from_url("https://tenant.example.com/api/v1/") == (
        "tenant.example.com"
    )


def test_get_tenant_id_from_url_handles_urls_without_scheme():
    assert get_tenant_id_from_url("tenant.example.com/api/v1/") == (
        "tenant.example.com"
    )


def test_make_tenable_id_scopes_provider_id_to_tenant():
    assert make_tenable_id("tenant.example.com", "asset-1") == (
        "tenant.example.com:asset-1"
    )
