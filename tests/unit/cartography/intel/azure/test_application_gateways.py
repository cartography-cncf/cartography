import pytest
from azure.mgmt.network.models import ApplicationGateway

from cartography.intel.azure import application_gateways
from tests.data.azure.application_gateway import MOCK_APPLICATION_GATEWAY_ARM
from tests.data.azure.application_gateway import MOCK_APPLICATION_GATEWAYS


@pytest.mark.parametrize(
    "transform",
    [
        lambda ag: application_gateways.transform_application_gateways([ag]),
        application_gateways.transform_frontend_ips,
        application_gateways.transform_backend_pools,
        application_gateways.transform_rules,
    ],
    ids=["gateway", "frontend_ips", "backend_pools", "rules"],
)
def test_transforms_read_current_sdk_shape(transform):
    current_sdk = ApplicationGateway(MOCK_APPLICATION_GATEWAY_ARM).as_dict()

    expected = transform(MOCK_APPLICATION_GATEWAYS[0])

    assert expected
    assert transform(current_sdk) == expected
