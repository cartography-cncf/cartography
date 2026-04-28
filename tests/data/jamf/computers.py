COMPUTERS_RESPONSE = {
    "results": [
        {
            "id": 7001,
            "udid": "simpsons-mac-udid-7001",
            "general": {
                "name": "Springfield-Admin-Mac-01",
                "platform": "macOS",
                "reportDate": "2026-04-16T16:00:00Z",
                "lastContactTime": "2026-04-16T15:55:00Z",
                "site": {"name": "Springfield HQ"},
                "supervised": True,
                "userApprovedMdm": True,
                "declarativeDeviceManagementEnabled": True,
                "enrolledViaAutomatedDeviceEnrollment": True,
                "remoteManagement": {"managed": True},
            },
            "hardware": {
                "serialNumber": "C02SPRING001",
                "model": "MacBook Pro",
                "modelIdentifier": "Mac15,9",
            },
            "operatingSystem": {
                "name": "macOS",
                "version": "14.5",
                "build": "23F79",
            },
            "security": {
                "activationLockEnabled": True,
                "recoveryLockEnabled": True,
                "bootstrapTokenEscrowedStatus": "ESCROWED",
                "firewallEnabled": True,
                "gatekeeperStatus": "APP_STORE_AND_IDENTIFIED_DEVELOPERS",
                "secureBootLevel": "FULL_SECURITY",
                "sipStatus": "ENABLED",
            },
            "diskEncryption": {"fileVault2Enabled": True},
            "userAndLocation": {
                "username": "h.simpson",
                "realname": "Homer Simpson",
                "email": "h.simpson@springfield.example",
            },
            "groupMemberships": [
                {
                    "groupId": 101,
                    "groupName": "Springfield Managed Macs",
                    "groupDescription": "All managed macOS endpoints",
                    "smartGroup": True,
                },
                {
                    "groupId": 102,
                    "groupName": "Sector 7G Workstations",
                    "groupDescription": "Power plant engineering fleet",
                    "smartGroup": False,
                },
            ],
        },
        {
            "id": 7002,
            "udid": "simpsons-mac-udid-7002",
            "general": {
                "name": "Springfield-Design-Mac-02",
                "platform": "macOS",
                "reportDate": "2026-04-16T14:00:00Z",
                "lastContactTime": "2026-04-16T13:52:00Z",
                "site": {"name": "Springfield Annex"},
                "supervised": False,
                "userApprovedMdm": False,
                "declarativeDeviceManagementEnabled": False,
                "enrolledViaAutomatedDeviceEnrollment": False,
                "remoteManagement": {"managed": False},
            },
            "hardware": {
                "serialNumber": "C02SPRING002",
                "model": "MacBook Air",
                "modelIdentifier": "Mac14,2",
            },
            "operatingSystem": {
                "name": "macOS",
                "version": "13.6.7",
                "build": "22G720",
            },
            "security": {
                "activationLockEnabled": False,
                "recoveryLockEnabled": False,
                "bootstrapTokenEscrowedStatus": "NOT_ESCROWED",
                "firewallEnabled": False,
                "gatekeeperStatus": "APP_STORE_ONLY",
                "secureBootLevel": "MEDIUM_SECURITY",
                "sipStatus": "DISABLED",
            },
            "diskEncryption": {"fileVault2Enabled": False},
            "userAndLocation": {
                "username": "l.simpson",
                "realname": "Lisa Simpson",
                "email": "l.simpson@springfield.example",
            },
            "groupMemberships": [
                {
                    "groupId": 101,
                    "groupName": "Springfield Managed Macs",
                    "groupDescription": "All managed macOS endpoints",
                    "smartGroup": True,
                }
            ],
        },
    ],
    "totalCount": 2,
}

COMPUTERS = COMPUTERS_RESPONSE["results"]
