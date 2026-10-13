from unittest.mock import Mock

import cartography.intel.tailscale.devices


def test_get_device_posture_attributes_handles_scalar_and_object_values():
    # Arrange
    api_session = Mock()
    response = Mock()
    response.json.return_value = {
        "attributes": {
            "sentinelOne:infected": "true",
            "falcon:ztaScore": {"value": "85"},
            "intune:complianceState": {"value": "compliant"},
            "fleet:present": True,
        },
    }
    response.raise_for_status.return_value = None
    api_session.get.return_value = response

    devices = [
        {
            "nodeId": "device-1",
            "os": "linux",
            "clientVersion": "v1.80.0",
        },
    ]

    # Act
    results = cartography.intel.tailscale.devices.get_device_posture_attributes(
        api_session,
        "https://fake.tailscale.com",
        devices,
    )

    # Assert
    assert results == {
        "device-1": {
            "node:os": "linux",
            "node:tsVersion": "1.80.0",
            "sentinelOne:infected": True,
            "falcon:ztaScore": 85,
            "intune:complianceState": "compliant",
            "fleet:present": True,
        },
    }
