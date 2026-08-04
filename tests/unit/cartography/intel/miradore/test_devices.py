from datetime import datetime

import pytest

from cartography.intel.miradore.devices import transform
from cartography.intel.miradore.devices import transform_deployments
from tests.data.miradore.devices import DEVICES

TEST_SITE_NAME = "simpsoncorp"


def _by_id(devices: list[dict], miradore_id: int) -> dict:
    return next(d for d in devices if d["miradore_id"] == miradore_id)


def test_transform_flattens_the_child_items() -> None:
    devices = transform(DEVICES, TEST_SITE_NAME)

    macbook = _by_id(devices, 1001)
    assert macbook["hostname"] == "marge-macbook"
    assert macbook["serial_number"] == "C02XY1234567"
    assert macbook["manufacturer"] == "Apple"
    assert macbook["model"] == "MacBookPro18,3"
    assert macbook["platform"] == "macOS"
    assert macbook["os_platform"] == "macOS"
    assert macbook["os_version"] == "15.5"
    assert macbook["os_build"] == "24F74"
    assert macbook["client_id"] == 5001
    assert macbook["management_type"] == "MacBoth"
    assert macbook["user_id"] == "simpsoncorp/2001"
    assert macbook["organization_id"] == "simpsoncorp/3001"
    assert macbook["location_id"] == "simpsoncorp/4001"
    assert macbook["category_id"] == 6001
    assert macbook["category_name"] == "Laptops"


def test_transform_falls_back_to_the_device_serial_number() -> None:
    """`Device.SerialNo` wins over the hardware serial when the inventory serial is absent."""
    iphone = _by_id(transform(DEVICES, TEST_SITE_NAME), 1002)

    assert iphone["serial_number"] == "F2LX9ABCDEFG"


def test_transform_parses_dates_into_datetimes() -> None:
    macbook = _by_id(transform(DEVICES, TEST_SITE_NAME), 1001)

    assert macbook["created"] == datetime(2024, 1, 5, 9, 12, 33)
    assert macbook["last_reported"] == datetime(2026, 8, 1, 7, 45, 10)
    assert macbook["warranty_end_date"] == datetime(2026, 12, 1, 0, 0, 0)
    # Not reported for this device.
    assert macbook["lease_end_date"] is None


def test_transform_collects_tag_names() -> None:
    devices = transform(DEVICES, TEST_SITE_NAME)

    # xmltodict collapses a single <Tag> element to a dict rather than a list.
    assert _by_id(devices, 1001)["tag_names"] == ["simpsoncorp/engineering"]
    assert _by_id(devices, 1002)["tag_names"] == [
        "simpsoncorp/engineering",
        "simpsoncorp/byod",
    ]
    assert _by_id(devices, 1003)["tag_names"] == []


def test_transform_reads_the_platform_specific_security_posture() -> None:
    devices = transform(DEVICES, TEST_SITE_NAME)

    macbook = _by_id(devices, 1001)
    assert macbook["passcode_set"] == "Yes"
    assert macbook["encryption_status"] == "Enabled"
    assert macbook["macos_activation_lock_enabled"] is True
    assert macbook["ios_supervised"] is None

    iphone = _by_id(devices, 1002)
    assert iphone["ios_supervised"] is True
    assert iphone["ios_software_jailbroken"] is False
    assert iphone["ios_hardware_encryption"] == "BlockAndFileLevelEncryption"
    assert iphone["ios_passcode_present"] == "Yes"

    pixel = _by_id(devices, 1003)
    assert pixel["android_rooted"] == "Rooted"
    assert pixel["android_passcode_sufficient"] == "No"
    assert pixel["android_password_min_length"] == 4
    assert pixel["android_security_patch_level"] == "2026-06-01"

    workstation = _by_id(devices, 1004)
    assert workstation["windows_secure_boot_state"] == "Disabled"
    assert workstation["windows_antivirus_status"] == "Disabled"
    assert workstation["windows_tpm_specification_version"] == "2.0"
    assert workstation["windows_complies_with_enterprise_encryption_policy"] is False


def test_transform_deployments_flattens_every_device() -> None:
    deployments = transform_deployments(DEVICES, TEST_SITE_NAME)

    assert {deployment["id"] for deployment in deployments} == {
        "simpsoncorp/7001",
        "simpsoncorp/7002",
        "simpsoncorp/7003",
    }
    installed = next(d for d in deployments if d["miradore_id"] == 7001)
    assert installed["device_id"] == "simpsoncorp/1001"
    assert installed["config_profile_id"] == "simpsoncorp/8001"
    assert installed["status"] == "Installed"
    assert installed["deployment_trigger"] == "Administrator"
    assert installed["deployment_time"] == datetime(2024, 2, 1, 10, 0, 0)

    # xmltodict collapses the single deployment on device 1002 to a dict.
    single = next(d for d in deployments if d["miradore_id"] == 7003)
    assert single["device_id"] == "simpsoncorp/1002"
    assert single["config_profile_id"] == "simpsoncorp/8002"


def test_transform_handles_an_empty_result() -> None:
    assert transform([], TEST_SITE_NAME) == []
    assert transform_deployments([], TEST_SITE_NAME) == []


def test_transform_rejects_a_device_without_an_id() -> None:
    """A null graph identity would reach the ingestion MERGE, so fail at the boundary."""
    with pytest.raises(KeyError):
        transform([{"InvDevice": {"DeviceName": "no-id-device"}}], TEST_SITE_NAME)


def test_transform_deployments_rejects_a_deployment_without_an_id() -> None:
    with pytest.raises(KeyError):
        transform_deployments(
            [{"ID": "1001", "ConfigProfileDeployment": {"Status": "Installed"}}],
            TEST_SITE_NAME,
        )
