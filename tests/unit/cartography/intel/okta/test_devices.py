import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from okta.models.device_list import DeviceList

from cartography.intel.okta.devices import _get_okta_devices
from cartography.intel.okta.devices import _transform_okta_devices
from tests.data.okta.devices import DEVICES


def test_transform_okta_devices() -> None:
    # Arrange
    raw_devices = [DeviceList.model_validate(device) for device in DEVICES]

    # Act
    devices, relationships = _transform_okta_devices(raw_devices)

    # Assert
    assert devices[0] == {
        "id": "device-001",
        "status": "ACTIVE",
        "created": "2025-01-15T10:30:00+00:00",
        "okta_last_updated": "2025-12-01T14:22:00+00:00",
        "display_name": "Work MacBook",
        "platform": "MACOS",
        "serial_number": "SERIAL-001",
        "sid": None,
        "manufacturer": "Apple",
        "model": "MacBook Pro",
        "os_version": "15.1",
        "registered": True,
        "managed": True,
        "secure_hardware_present": True,
        "disk_encryption_type": "ALL_INTERNAL_VOLUMES",
        "integrity_jailbreak": False,
        "imei": None,
        "meid": None,
        "udid": "UDID-001",
        "tpm_public_key_hash": None,
        "resource_type": "UDDevice",
        "resource_display_name": "Work MacBook",
        "resource_display_name_sensitive": False,
        "resource_alternate_id": None,
    }
    assert relationships == [
        {
            "device_id": "device-001",
            "user_id": "user-001",
            "management_status": "MANAGED",
            "screen_lock_type": "BIOMETRIC",
            "enrolled_at": "2025-01-16T10:30:00Z",
        },
    ]


def test_transform_okta_device_without_user() -> None:
    # Arrange
    raw_device = DeviceList.model_validate(DEVICES[1])

    # Act
    devices, relationships = _transform_okta_devices([raw_device])

    # Assert
    assert devices[0]["id"] == "device-002"
    assert devices[0]["manufacturer"] is None
    assert relationships == []


def test_get_okta_devices_expands_user_summary() -> None:
    # Arrange
    okta_client = MagicMock()
    okta_client.list_devices = AsyncMock(return_value=([], None, None))

    # Act
    devices = asyncio.run(_get_okta_devices(okta_client))

    # Assert
    assert devices == []
    okta_client.list_devices.assert_awaited_once_with(
        limit=200,
        after=None,
        expand="userSummary",
    )
