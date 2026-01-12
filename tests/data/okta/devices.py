# Test data for Okta Devices API
# Based on: https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Device/#tag/Device/operation/listDevices

# Sample response from GET /api/v1/devices?expand=userSummary
SAMPLE_DEVICES = [
    {
        "id": "guo4a5u7YAHhjXrMK0g4",
        "status": "CREATED",
        "created": "2019-10-02T18:03:07.000Z",
        "lastUpdated": "2019-10-02T18:03:07.000Z",
        "profile": {
            "displayName": "Example device name 1",
            "platform": "WINDOWS",
            "serialNumber": "XXDDRFCFRGF3M8MD6D",
            "sid": "S-1-11-111",
            "registered": True,
            "secureHardwarePresent": False,
            "diskEncryptionType": "ALL_INTERNAL_VOLUMES",
        },
        "resourceType": "UDDevice",
        "resourceDisplayName": {
            "value": "Example device name 1",
            "sensitive": False,
        },
        "resourceAlternateId": None,
        "resourceId": "guo4a5u7YAHhjXrMK0g4",
        "_links": {
            "activate": {
                "href": "https://test.okta.com/api/v1/devices/guo4a5u7YAHhjXrMK0g4/lifecycle/activate",
                "hints": {
                    "allow": [
                        "POST",
                    ],
                },
            },
            "self": {
                "href": "https://test.okta.com/api/v1/devices/guo4a5u7YAHhjXrMK0g4",
                "hints": {
                    "allow": [
                        "GET",
                        "PATCH",
                        "PUT",
                    ],
                },
            },
            "users": {
                "href": "https://test.okta.com/api/v1/devices/guo4a5u7YAHhjXrMK0g4/users",
                "hints": {
                    "allow": [
                        "GET",
                    ],
                },
            },
        },
        "_embedded": {
            "users": [],
        },
    },
    {
        "id": "guo4a5u7YAHhjXrMK0g5",
        "status": "ACTIVE",
        "created": "2023-06-21T23:24:02.000Z",
        "lastUpdated": "2023-06-21T23:24:02.000Z",
        "profile": {
            "displayName": "Example device name 2",
            "platform": "ANDROID",
            "manufacturer": "Google",
            "model": "Pixel 6",
            "osVersion": "13:2023-05-05",
            "registered": True,
            "secureHardwarePresent": True,
            "diskEncryptionType": "USER",
        },
        "resourceType": "UDDevice",
        "resourceDisplayName": {
            "value": "Example device name 2",
            "sensitive": False,
        },
        "resourceAlternateId": None,
        "resourceId": "guo4a5u7YAHhjXrMK0g5",
        "_links": {
            "activate": {
                "href": "https://test.okta.com/api/v1/devices/guo4a5u7YAHhjXrMK0g5/lifecycle/activate",
                "hints": {
                    "allow": [
                        "POST",
                    ],
                },
            },
            "self": {
                "href": "https://test.okta.com/api/v1/devices/guo4a5u7YAHhjXrMK0g5",
                "hints": {
                    "allow": [
                        "GET",
                        "PATCH",
                        "PUT",
                    ],
                },
            },
            "users": {
                "href": "https://test.okta.com/api/v1/devices/guo4a5u7YAHhjXrMK0g5/users",
                "hints": {
                    "allow": [
                        "GET",
                    ],
                },
            },
        },
        "_embedded": {
            "users": [
                {
                    "managementStatus": "MANAGED",
                    "created": "2021-10-01T16:52:41.000Z",
                    "screenLockType": "BIOMETRIC",
                    "user": {
                        "id": "00u17vh0q8ov8IU881d7",
                        "realmId": "00u17vh0q8ov8IU8T0g5",
                        "profile": {
                            "firstName": "fname",
                            "lastName": "lname",
                            "login": "email@email.com",
                            "email": "email@email.com",
                        },
                        "_links": {
                            "self": {
                                "href": "https://test.okta.com/api/v1/users/00u17vh0q8ov8IU881d7",
                            },
                        },
                    },
                },
            ],
        },
    },
]
