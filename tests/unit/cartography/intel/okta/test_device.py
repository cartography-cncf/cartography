from cartography.intel.okta.devices import transform_okta_device
from cartography.intel.okta.devices import transform_okta_device_users
from tests.data.okta.devices import SAMPLE_DEVICES


def test_transform_okta_device_windows():
    """Test transformation of a Windows device."""
    device_data = SAMPLE_DEVICES[0]  # Windows device

    result = transform_okta_device(device_data)

    assert result["id"] == "guo4a5u7YAHhjXrMK0g4"
    assert result["status"] == "CREATED"
    assert result["created"] == "2019-10-02T18:03:07.000Z"
    assert result["last_updated"] == "2019-10-02T18:03:07.000Z"
    assert result["display_name"] == "Example device name 1"
    assert result["platform"] == "WINDOWS"
    assert result["serial_number"] == "XXDDRFCFRGF3M8MD6D"
    assert result["sid"] == "S-1-11-111"
    assert result["registered"] is True
    assert result["secure_hardware_present"] is False
    assert result["disk_encryption_type"] == "ALL_INTERNAL_VOLUMES"
    assert result["resource_type"] == "UDDevice"
    assert result["resource_display_name"] == "Example device name 1"
    assert result["resource_display_name_sensitive"] is False


def test_transform_okta_device_android():
    """Test transformation of an Android device."""
    device_data = SAMPLE_DEVICES[1]  # Android device

    result = transform_okta_device(device_data)

    assert result["id"] == "guo4a5u7YAHhjXrMK0g5"
    assert result["status"] == "ACTIVE"
    assert result["created"] == "2023-06-21T23:24:02.000Z"
    assert result["last_updated"] == "2023-06-21T23:24:02.000Z"
    assert result["display_name"] == "Example device name 2"
    assert result["platform"] == "ANDROID"
    assert result["manufacturer"] == "Google"
    assert result["model"] == "Pixel 6"
    assert result["os_version"] == "13:2023-05-05"
    assert result["registered"] is True
    assert result["secure_hardware_present"] is True
    assert result["disk_encryption_type"] == "USER"


def test_transform_okta_device_with_minimal_values():
    """Test transformation of a device with only required fields."""
    device_data = {
        "id": "device123",
        "status": "CREATED",
        "profile": {
            "platform": "IOS",
        },
    }

    result = transform_okta_device(device_data)

    assert result["id"] == "device123"
    assert result["status"] == "CREATED"
    assert result["platform"] == "IOS"
    assert result["created"] is None
    assert result["last_updated"] is None
    assert result["display_name"] is None
    assert result["manufacturer"] is None
    assert result["model"] is None


def test_transform_okta_device_users_with_users():
    """Test extraction of user-device relationships."""
    device_data = SAMPLE_DEVICES[1]  # Android device with user

    result = transform_okta_device_users(device_data)

    assert len(result) == 1
    assert result[0]["device_id"] == "guo4a5u7YAHhjXrMK0g5"
    assert result[0]["user_id"] == "00u17vh0q8ov8IU881d7"
    assert result[0]["management_status"] == "MANAGED"
    assert result[0]["screen_lock_type"] == "BIOMETRIC"
    assert result[0]["enrolled_at"] == "2021-10-01T16:52:41.000Z"


def test_transform_okta_device_users_with_no_users():
    """Test extraction when device has no users."""
    device_data = SAMPLE_DEVICES[0]  # Windows device with no users

    result = transform_okta_device_users(device_data)

    assert result == []


def test_transform_okta_device_users_with_no_embedded():
    """Test extraction when _embedded field is missing."""
    device_data = {
        "id": "device789",
    }

    result = transform_okta_device_users(device_data)

    assert result == []


def test_transform_okta_device_users_with_partial_data():
    """Test extraction when user data has missing optional fields."""
    device_data = {
        "id": "device999",
        "_embedded": {
            "users": [
                {
                    "user": {
                        "id": "user999",
                    },
                    # Missing managementStatus, screenLockType, created
                },
            ],
        },
    }

    result = transform_okta_device_users(device_data)

    assert len(result) == 1
    assert result[0]["device_id"] == "device999"
    assert result[0]["user_id"] == "user999"
    assert result[0]["management_status"] is None
    assert result[0]["screen_lock_type"] is None
    assert result[0]["enrolled_at"] is None
