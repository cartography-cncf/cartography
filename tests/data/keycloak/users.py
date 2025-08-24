KEYCLOAK_USERS = [
    {
        "id": "b34866c4-7c54-439d-82ab-f8c21bd2d81a",
        "username": "hjsimpson",
        "firstName": "Homer",
        "lastName": "Simpson",
        "email": "hjsimpson@simpson.corp",
        "emailVerified": True,
        "userProfileMetadata": {
            "attributes": [
                {
                    "name": "username",
                    "displayName": "${username}",
                    "required": True,
                    "readOnly": True,
                    "validators": {
                        "username-prohibited-characters": {"ignore.empty.value": True},
                        "multivalued": {"max": "1"},
                        "length": {"max": 255, "ignore.empty.value": True, "min": 3},
                        "up-username-not-idn-homograph": {"ignore.empty.value": True},
                    },
                    "multivalued": False,
                },
                {
                    "name": "email",
                    "displayName": "${email}",
                    "required": False,
                    "readOnly": False,
                    "validators": {
                        "multivalued": {"max": "1"},
                        "length": {"max": 255, "ignore.empty.value": True},
                        "email": {"ignore.empty.value": True},
                    },
                    "multivalued": False,
                },
                {
                    "name": "firstName",
                    "displayName": "${firstName}",
                    "required": False,
                    "readOnly": False,
                    "validators": {
                        "person-name-prohibited-characters": {
                            "ignore.empty.value": True
                        },
                        "multivalued": {"max": "1"},
                        "length": {"max": 255, "ignore.empty.value": True},
                    },
                    "multivalued": False,
                },
                {
                    "name": "lastName",
                    "displayName": "${lastName}",
                    "required": False,
                    "readOnly": False,
                    "validators": {
                        "person-name-prohibited-characters": {
                            "ignore.empty.value": True
                        },
                        "multivalued": {"max": "1"},
                        "length": {"max": 255, "ignore.empty.value": True},
                    },
                    "multivalued": False,
                },
            ],
            "groups": [
                {
                    "name": "user-metadata",
                    "displayHeader": "User metadata",
                    "displayDescription": "Attributes, which refer to user metadata",
                }
            ],
        },
        "enabled": True,
        "createdTimestamp": 1754315297382,
        "totp": False,
        "disableableCredentialTypes": [],
        "requiredActions": [],
        "notBefore": 0,
        "access": {"manage": True},
    },
    {
        "id": "ccd37f3c-57de-423a-879e-f376de2839ec",
        "username": "mbsimpson",
        "firstName": "Marge",
        "lastName": "Simpson",
        "email": "mbsimpson@simpson.corp",
        "emailVerified": True,
        "userProfileMetadata": {
            "attributes": [
                {
                    "name": "username",
                    "displayName": "${username}",
                    "required": True,
                    "readOnly": True,
                    "validators": {
                        "username-prohibited-characters": {"ignore.empty.value": True},
                        "multivalued": {"max": "1"},
                        "length": {"max": 255, "ignore.empty.value": True, "min": 3},
                        "up-username-not-idn-homograph": {"ignore.empty.value": True},
                    },
                    "multivalued": False,
                },
                {
                    "name": "email",
                    "displayName": "${email}",
                    "required": False,
                    "readOnly": False,
                    "validators": {
                        "multivalued": {"max": "1"},
                        "length": {"max": 255, "ignore.empty.value": True},
                        "email": {"ignore.empty.value": True},
                    },
                    "multivalued": False,
                },
                {
                    "name": "firstName",
                    "displayName": "${firstName}",
                    "required": False,
                    "readOnly": False,
                    "validators": {
                        "person-name-prohibited-characters": {
                            "ignore.empty.value": True
                        },
                        "multivalued": {"max": "1"},
                        "length": {"max": 255, "ignore.empty.value": True},
                    },
                    "multivalued": False,
                },
                {
                    "name": "lastName",
                    "displayName": "${lastName}",
                    "required": False,
                    "readOnly": False,
                    "validators": {
                        "person-name-prohibited-characters": {
                            "ignore.empty.value": True
                        },
                        "multivalued": {"max": "1"},
                        "length": {"max": 255, "ignore.empty.value": True},
                    },
                    "multivalued": False,
                },
            ],
            "groups": [
                {
                    "name": "user-metadata",
                    "displayHeader": "User metadata",
                    "displayDescription": "Attributes, which refer to user metadata",
                }
            ],
        },
        "enabled": True,
        "createdTimestamp": 1754315187011,
        "totp": False,
        "disableableCredentialTypes": [],
        "requiredActions": [],
        "notBefore": 0,
        "access": {"manage": True},
    },
]
