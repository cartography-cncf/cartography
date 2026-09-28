from cartography.intel.microsoft.o365.licenses import transform_licenses
from tests.data.microsoft.entra.users import TEST_TENANT_ID
from tests.data.microsoft.o365.licenses import make_subscribed_skus
from tests.data.microsoft.o365.licenses import MOCK_SUBSCRIBED_SKUS


def test_transform_licenses():
    """Ensure transform_licenses flattens SKUs and scopes SP IDs."""
    licenses, service_plans = transform_licenses(MOCK_SUBSCRIBED_SKUS, TEST_TENANT_ID)

    assert len(licenses) == 2
    assert {lic["sku_part_number"] for lic in licenses} == {
        "ENTERPRISEPREMIUM",
        "EMS",
    }

    # EXCHANGE appears in both SKUs but is deduplicated
    assert len(service_plans) == 4
    exchange_plan = next(
        sp for sp in service_plans if sp["service_plan_name"] == "EXCHANGE_S_ENTERPRISE"
    )
    assert len(exchange_plan["license_ids"]) == 2

    # Service plan IDs are scoped to tenant
    for sp in service_plans:
        assert sp["id"].startswith(f"{TEST_TENANT_ID}-")
        assert sp["service_plan_id"]


def test_transform_licenses_tenant_scoped_sku_ids():
    """Ensure factory-generated SKU IDs follow {tenantId}_{skuId} format."""
    skus = make_subscribed_skus("tenant-aaa")
    licenses, _ = transform_licenses(skus, "tenant-aaa")

    for lic in licenses:
        assert lic["id"].startswith("tenant-aaa_")
