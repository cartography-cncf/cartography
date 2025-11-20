MOCK_GSUITE_USERS_RESPONSE = [
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
                    "fullName": "Alice Admin",
                    "familyName": "Admin",
                    "givenName": "Alice",
                },
                "orgUnitPath": "/",
                "primaryEmail": "alice@example.com",
                "suspended": False,
                "thumbnailPhotoEtag": "photo-etag-1",
                "thumbnailPhotoUrl": "https://example.com/photo1.jpg",
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
                    "fullName": "Bob Builder",
                    "familyName": "Builder",
                    "givenName": "Bob",
                },
                "orgUnitPath": "/Engineering",
                "primaryEmail": "bob@example.com",
                "suspended": False,
                "thumbnailPhotoEtag": "photo-etag-2",
                "thumbnailPhotoUrl": "https://example.com/photo2.jpg",
            },
        ],
    },
]

MOCK_GSUITE_GROUPS_RESPONSE = [
    {
        "id": "group-engineering",
        "adminCreated": True,
        "description": "Engineering team",
        "directMembersCount": 3,
        "email": "engineering@example.com",
        "etag": "etag-group-1",
        "kind": "admin#directory#group",
        "name": "Engineering",
    },
    {
        "id": "group-operations",
        "adminCreated": False,
        "description": "Operations sub-team",
        "directMembersCount": 1,
        "email": "operations@example.com",
        "etag": "etag-group-2",
        "kind": "admin#directory#group",
        "name": "Operations",
    },
]


# See: https://developers.google.com/workspace/admin/directory/v1/guides/manage-group-members#json-response_3
MOCK_GSUITE_MEMBERS_BY_GROUP_EMAIL = {
    "engineering@example.com": [
        {
            "id": "user-1",
            "email": "user-1@example.com",
            "type": "USER",
            "role": "MEMBER",
        },
        {
            "id": "user-2",
            "email": "user-2@example.com",
            "type": "USER",
            "role": "MEMBER",
        },
        {
            "id": "group-operations",
            "email": "operations@example.com",
            "type": "GROUP",
            "role": "MEMBER",
        },
    ],
    "operations@example.com": [
        {
            "id": "user-2",
            "email": "user-2@example.com",
            "type": "USER",
            "role": "MEMBER",
        },
    ],
}
