MOCK_GOOGLEWORKSPACE_USERS_RESPONSE = [
    {
        "users": [
            {
                "id": "user-1",
                "agreedToTerms": True,
                "archived": False,
                "changePasswordAtNextLogin": False,
                "creationTime": "2023-01-01T00:00:00.000Z",
                "customerId": "customer-123",
                "etag": "etag-user-1",
                "includeInGlobalAddressList": True,
                "ipWhitelisted": False,
                "isAdmin": True,
                "isDelegatedAdmin": False,
                "isEnforcedIn2Sv": True,
                "isEnrolledIn2Sv": True,
                "isMailboxSetup": True,
                "kind": "admin#directory#user",
                "lastLoginTime": "2024-01-01T12:34:56.000Z",
                "name": {
                    "fullName": "Marge Simpson",
                    "familyName": "Simpson",
                    "givenName": "Marge",
                },
                "orgUnitPath": "/",
                "primaryEmail": "mbsimpson@simpson.corp",
                "suspended": False,
                "thumbnailPhotoEtag": "photo-etag-1",
                "thumbnailPhotoUrl": "https://simpson.corp/photos/mbsimpson.jpg",
                "organizations": [
                    {
                        "name": "Simpson Corp",
                        "title": "Chief Executive Officer",
                        "primary": True,
                        "department": "Management",
                    }
                ],
            },
            {
                "id": "user-2",
                "agreedToTerms": True,
                "archived": False,
                "changePasswordAtNextLogin": False,
                "creationTime": "2023-02-01T00:00:00.000Z",
                "customerId": "customer-123",
                "etag": "etag-user-2",
                "includeInGlobalAddressList": True,
                "ipWhitelisted": False,
                "isAdmin": False,
                "isDelegatedAdmin": False,
                "isEnforcedIn2Sv": False,
                "isEnrolledIn2Sv": False,
                "isMailboxSetup": True,
                "kind": "admin#directory#user",
                "lastLoginTime": "2024-02-01T06:00:00.000Z",
                "name": {
                    "fullName": "Homer Simpson",
                    "familyName": "Simpson",
                    "givenName": "Homer",
                },
                "orgUnitPath": "/Engineering",
                "primaryEmail": "hjsimpson@simpson.corp",
                "suspended": False,
                "thumbnailPhotoEtag": "photo-etag-2",
                "thumbnailPhotoUrl": "https://simpson.corp/photos/hjsimpson.jpg",
            },
        ],
    },
]

MOCK_GOOGLEWORKSPACE_GROUPS_RESPONSE = [
    {
        "id": "group-engineering",
        "adminCreated": True,
        "description": "Engineering team",
        "directMembersCount": 3,
        "email": "engineering@simpson.corp",
        "etag": "etag-group-1",
        "kind": "admin#directory#group",
        "name": "Engineering",
    },
    {
        "id": "group-operations",
        "adminCreated": False,
        "description": "Operations sub-team",
        "directMembersCount": 1,
        "email": "operations@simpson.corp",
        "etag": "etag-group-2",
        "kind": "admin#directory#group",
        "name": "Operations",
    },
]


# See: https://developers.google.com/workspace/admin/directory/v1/guides/manage-group-members#json-response_3
MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL = {
    "engineering@simpson.corp": [
        {
            "id": "user-1",
            "email": "mbsimpson@simpson.corp",
            "type": "USER",
            "role": "MEMBER",
        },
        {
            "id": "user-2",
            "email": "hjsimpson@simpson.corp",
            "type": "USER",
            "role": "MEMBER",
        },
        {
            "id": "group-operations",
            "email": "operations@simpson.corp",
            "type": "GROUP",
            "role": "MEMBER",
        },
    ],
    "operations@simpson.corp": [
        {
            "id": "user-2",
            "email": "hjsimpson@simpson.corp",
            "type": "USER",
            "role": "MEMBER",
        },
    ],
}
