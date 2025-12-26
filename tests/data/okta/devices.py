def create_test_device():
    return {
        "id": "device-001",
        "status": "ACTIVE",
        "created": "2023-01-15T10:30:00.000Z",
        "lastUpdated": "2023-12-01T14:22:00.000Z",
        "profile": {
            "displayName": "iPhone 14 Pro",
            "platform": "IOS",
            "manufacturer": "Apple",
            "model": "iPhone",
            "serialNumber": "ABC123XYZ",
            "osVersion": "17.1.0",
            "userAgent": "Mozilla/5.0...",
            "deviceId": "device-id-123",
        },
        "_embedded": {
            "user": {
                "id": "user-001",
            },
        },
        "_links": {
            "self": {
                "href": "https://test.okta.com/api/v1/devices/device-001",
            },
            "user": {
                "href": "https://test.okta.com/api/v1/users/user-001",
            },
        },
    }


def create_test_device_no_user():
    """
    test device without user association
    """
    device = create_test_device()
    device["id"] = "device-no-user"
    device["_embedded"] = {}
    device["_links"].pop("user", None)
    return device
