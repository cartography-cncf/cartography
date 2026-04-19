GROUPS_RESPONSE = {
    "results": [
        {
            "groupDescription": "All managed macOS endpoints",
            "groupJamfProId": "101",
            "groupName": "Springfield Managed Macs",
            "groupPlatformId": "platform-computer-101",
            "groupType": "COMPUTER",
            "membershipCount": 42,
            "smart": True,
        },
        {
            "groupDescription": "Power plant engineering fleet",
            "groupJamfProId": "102",
            "groupName": "Sector 7G Workstations",
            "groupPlatformId": "platform-computer-102",
            "groupType": "COMPUTER",
            "membershipCount": 12,
            "smart": False,
        },
        {
            "groupDescription": "Managed iPhone fleet",
            "groupJamfProId": "201",
            "groupName": "Springfield iPhones",
            "groupPlatformId": "platform-mobile-201",
            "groupType": "MOBILE",
            "membershipCount": 85,
            "smart": True,
        },
        {
            "groupDescription": "Managed iPad fleet",
            "groupJamfProId": "202",
            "groupName": "Springfield iPads",
            "groupPlatformId": "platform-mobile-202",
            "groupType": "MOBILE",
            "membershipCount": 19,
            "smart": True,
        },
    ],
    "totalCount": 4,
}

GROUPS = GROUPS_RESPONSE["results"]
