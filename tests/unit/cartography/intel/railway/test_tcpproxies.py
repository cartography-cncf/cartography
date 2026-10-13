from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.railway.network.tcpproxies

PRODUCTION_ENV_ID = "44444444-4444-4444-4444-444444444444"
WEB_SERVICE_ID = "66666666-6666-6666-6666-666666666666"
POSTGRES_SERVICE_ID = "77777777-7777-7777-7777-777777777777"
WEB_INSTANCE_ID = "88888888-8888-8888-8888-888888888888"
POSTGRES_INSTANCE_ID = "99999999-9999-9999-9999-999999999999"
WEB_PROXY_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
POSTGRES_PROXY_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"


def test_tcp_proxy_batch_maps_aliases_back_to_instances():
    # The alias index is the only link between a proxy and the instance that owns it, so a
    # mismatch here would silently attach proxies to the wrong service.
    instances = [
        {
            "id": WEB_INSTANCE_ID,
            "serviceId": WEB_SERVICE_ID,
            "environmentId": PRODUCTION_ENV_ID,
        },
        {
            "id": POSTGRES_INSTANCE_ID,
            "serviceId": POSTGRES_SERVICE_ID,
            "environmentId": PRODUCTION_ENV_ID,
        },
    ]
    response = {
        "p0": [{"id": WEB_PROXY_ID, "domain": "sakura.proxy.rlwy.net"}],
        "p1": [{"id": POSTGRES_PROXY_ID, "domain": "tokaido.proxy.rlwy.net"}],
    }

    with patch(
        "cartography.intel.railway.network.tcpproxies.call_railway_api",
        return_value=response,
    ):
        result = cartography.intel.railway.network.tcpproxies.get(
            Mock(),
            "https://backboard.railway.com/graphql/v2",
            instances,
        )

    assert result[WEB_INSTANCE_ID][0]["id"] == WEB_PROXY_ID
    assert result[WEB_INSTANCE_ID][0]["service_id"] == WEB_SERVICE_ID
    assert result[POSTGRES_INSTANCE_ID][0]["id"] == POSTGRES_PROXY_ID
    assert result[POSTGRES_INSTANCE_ID][0]["service_id"] == POSTGRES_SERVICE_ID


def test_tcp_proxy_get_handles_instances_without_proxies():
    instances = [
        {
            "id": WEB_INSTANCE_ID,
            "serviceId": WEB_SERVICE_ID,
            "environmentId": PRODUCTION_ENV_ID,
        },
    ]

    with patch(
        "cartography.intel.railway.network.tcpproxies.call_railway_api",
        return_value={"p0": []},
    ):
        result = cartography.intel.railway.network.tcpproxies.get(
            Mock(),
            "https://backboard.railway.com/graphql/v2",
            instances,
        )

    assert result == {WEB_INSTANCE_ID: []}
