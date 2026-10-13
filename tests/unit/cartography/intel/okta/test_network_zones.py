from cartography.intel.okta.network_zones import _transform_okta_network_zones
from tests.data.okta.network_zones import NETWORK_ZONES


def test_transform_okta_network_zones() -> None:
    # Act
    zones = {zone["id"]: zone for zone in _transform_okta_network_zones(NETWORK_ZONES)}

    # Assert
    assert zones["nzo-corp"] == {
        "id": "nzo-corp",
        "name": "Corporate egress",
        "type": "IP",
        "status": "ACTIVE",
        "usage": "POLICY",
        "system": False,
        "created": "2026-01-01T00:00:00.000Z",
        "okta_last_updated": "2026-01-01T00:00:00.000Z",
        "gateways": ["198.51.100.0/24", "203.0.113.10-203.0.113.20"],
        "proxies": ["192.0.2.10/32"],
        "use_as_exempt_list": False,
        "asns_include": [],
        "asns_exclude": [],
        "locations_include": [],
        "locations_exclude": [],
        "proxy_type": None,
        "ip_service_categories_include": [],
        "ip_service_categories_exclude": [],
    }
    assert zones["nzo-blocked-ips"]["proxies"] == []
    assert zones["nzo-tor"]["proxy_type"] == "TorAnonymizer"
    assert zones["nzo-tor"]["asns_include"] == ["64496", "64497"]
    assert zones["nzo-tor"]["locations_include"] == ["AQ", "US-AK"]
    assert zones["nzo-enhanced-dynamic"]["asns_exclude"] == ["64498"]
    assert zones["nzo-enhanced-dynamic"]["locations_exclude"] == ["CA"]
    assert zones["nzo-enhanced-dynamic"]["ip_service_categories_include"] == [
        "ALL_ANONYMIZERS",
        "FUTURE_CATEGORY",
    ]
