DEVICES = [
    {
        "id": "device-001",
        "status": "ACTIVE",
        "created": "2025-01-15T10:30:00Z",
        "lastUpdated": "2025-12-01T14:22:00Z",
        "profile": {
            "displayName": "Work MacBook",
            "platform": "MACOS",
            "manufacturer": "Apple",
            "model": "MacBook Pro",
            "serialNumber": "SERIAL-001",
            "osVersion": "15.1",
            "registered": True,
            "managed": True,
            "secureHardwarePresent": True,
            "diskEncryptionType": "ALL_INTERNAL_VOLUMES",
            "integrityJailbreak": False,
            "udid": "UDID-001",
        },
        "resourceType": "UDDevice",
        "resourceDisplayName": {
            "value": "Work MacBook",
            "sensitive": False,
        },
        "_embedded": {
            "users": [
                {
                    "managementStatus": "MANAGED",
                    "screenLockType": "BIOMETRIC",
                    "created": "2025-01-16T10:30:00Z",
                    "user": {
                        "id": "user-001",
                        "status": "ACTIVE",
                        "profile": {
                            "login": "alice@example.com",
                            "email": "alice@example.com",
                            "firstName": "Alice",
                            "lastName": "Example",
                        },
                    },
                },
            ],
        },
    },
    {
        "id": "device-002",
        "status": "SUSPENDED",
        "created": "2025-02-15T10:30:00Z",
        "lastUpdated": "2025-12-02T14:22:00Z",
        "profile": {
            "displayName": "Unassigned Windows Device",
            "platform": "WINDOWS",
            "serialNumber": "SERIAL-002",
            "registered": True,
        },
        "_embedded": {"users": []},
    },
]
