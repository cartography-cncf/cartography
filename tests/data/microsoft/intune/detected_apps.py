from msgraph.generated.models.detected_app import DetectedApp
from msgraph.generated.models.detected_app_platform_type import DetectedAppPlatformType
from msgraph.generated.models.managed_device import ManagedDevice

MOCK_DETECTED_APPS = [
    DetectedApp(
        id="app-001",
        display_name="Google Chrome",
        version="123.0.6312.86",
        size_in_byte=300000000,
        device_count=2,
        publisher="Google LLC",
        platform=DetectedAppPlatformType.MacOS,
        managed_devices=[
            ManagedDevice(id="device-001"),
            ManagedDevice(id="device-002"),
        ],
    ),
    DetectedApp(
        id="app-002",
        display_name="Tailscale",
        version="1.62.0",
        size_in_byte=50000000,
        device_count=1,
        publisher="Tailscale Inc.",
        platform=DetectedAppPlatformType.MacOS,
        managed_devices=[
            ManagedDevice(id="device-001"),
        ],
    ),
]
