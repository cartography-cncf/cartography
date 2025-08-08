KEYCLOAK_ORGANIZATIONS = [
    {
        "id": "6f326c1f-5c52-4293-9d33-b15eed19c220",
        "name": "springfield-powerplant-ltd",
        "alias": "springfield-powerplant-ltd",
        "enabled": True,
        "description": "",
        "domains": [{"name": "burns-lovers.com", "verified": False}],
        "_members": [
            {
                "id": "b34866c4-7c54-439d-82ab-f8c21bd2d81a",
                "username": "hjsimpson",
                "firstName": "Homer",
                "lastName": "Simpson",
                "email": "hjsimpson@simpson.corp",
                "emailVerified": True,
                "enabled": True,
                "createdTimestamp": 1754315297382,
                "totp": False,
                "disableableCredentialTypes": [],
                "requiredActions": [],
                "notBefore": 0,
                "membershipType": "UNMANAGED",
            }
        ],
        "_identity_providers": [
            {
                "alias": "clevercloud",
                "displayName": "",
                "internalId": "1522c1c3-a98c-45e5-99ee-948c666e37bf",
                "providerId": "clevercloud",
                "enabled": True,
                "updateProfileFirstLoginMode": "on",
                "trustEmail": False,
                "storeToken": False,
                "addReadTokenRoleOnCreate": False,
                "authenticateByDefault": False,
                "linkOnly": False,
                "hideOnLogin": False,
                "organizationId": "6f326c1f-5c52-4293-9d33-b15eed19c220",
                "config": {
                    "acceptsPromptNoneForwardFromClient": "False",
                    "clientId": "brYEI5jqq3yB3BPkqgSzIJbZV60KQB",
                    "disableUserInfo": "False",
                    "filteredByClaim": "False",
                    "syncMode": "LEGACY",
                    "clientSecret": "**********",
                    "caseSensitiveOriginalUsername": "False",
                    "kc.org.broker.redirect.mode.email-matches": "True",
                    "kc.org.domain": "burns-lovers.com",
                },
            }
        ],
    }
]
