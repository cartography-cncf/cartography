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
                "alias": "linkedin-openid-connect",
                "displayName": "LinkedIn",
                "internalId": "8e6bcacd-9592-4009-8fb2-aca89656ccc0",
                "providerId": "linkedin-openid-connect",
                "enabled": True,
                "updateProfileFirstLoginMode": "on",
                "trustEmail": False,
                "storeToken": False,
                "addReadTokenRoleOnCreate": False,
                "authenticateByDefault": False,
                "linkOnly": False,
                "hideOnLogin": False,
                "config": {
                    "syncMode": "LEGACY",
                    "clientSecret": "**********",
                    "clientId": "cdbbc355-f259-4ff5-a631-f32a541c4535",
                },
            }
        ],
    }
]
