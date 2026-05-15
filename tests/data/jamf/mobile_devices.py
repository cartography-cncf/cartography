MOBILE_DEVICES_RESPONSE = {
    "results": [
        {
            "mobileDeviceId": 9001,
            "deviceType": "iPhone",
            "general": {
                "displayName": "Bart-iPhone-01",
                "managed": True,
                "supervised": True,
                "lastInventoryUpdateDate": "2026-04-16T15:20:00Z",
                "lastEnrolledDate": "2025-09-01T08:00:00Z",
                "osVersion": "17.4.1",
                "osBuild": "21E236",
            },
            "hardware": {
                "serialNumber": "IPHONESPRING001",
                "model": "iPhone 15",
                "modelIdentifier": "iPhone15,4",
            },
            "security": {
                "activationLockEnabled": True,
                "bootstrapTokenEscrowed": True,
                "dataProtected": True,
                "hardwareEncryption": True,
                "jailBreakDetected": False,
                "lostModeEnabled": False,
                "passcodeCompliant": True,
                "passcodePresent": True,
            },
            "userAndLocation": {
                "username": "b.simpson",
                "realName": "Bart Simpson",
                "emailAddress": "b.simpson@springfield.example",
            },
            "groups": [
                {
                    "groupId": 201,
                    "groupName": "Springfield iPhones",
                    "groupDescription": "Managed iPhone fleet",
                    "smart": True,
                }
            ],
        },
        {
            "mobileDeviceId": 9002,
            "deviceType": "iPad",
            "general": {
                "displayName": "Lisa-iPad-01",
                "managed": True,
                "supervised": False,
                "lastInventoryUpdateDate": "2026-04-16T12:20:00Z",
                "lastEnrolledDate": "2025-03-15T08:00:00Z",
                "osVersion": "17.3",
                "osBuild": "21D50",
            },
            "hardware": {
                "serialNumber": "IPADSPRING001",
                "model": "iPad Pro",
                "modelIdentifier": "iPad14,3",
            },
            "security": {
                "activationLockEnabled": False,
                "bootstrapTokenEscrowed": False,
                "dataProtected": True,
                "hardwareEncryption": True,
                "jailBreakDetected": False,
                "lostModeEnabled": True,
                "passcodeCompliant": False,
                "passcodePresent": True,
            },
            "userAndLocation": {
                "username": "l.simpson",
                "realName": "Lisa Simpson",
                "emailAddress": "l.simpson@springfield.example",
            },
            "groups": None,
        },
    ],
    "totalCount": 2,
}

MOBILE_DEVICES = MOBILE_DEVICES_RESPONSE["results"]
