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
        "name": "groups/group-engineering",
        "groupKey": {
            "id": "engineering@simpson.corp",
        },
        "parent": "customers/ABC123CD",
        "displayName": "Engineering",
        "description": "Engineering team",
        "createTime": "2023-01-01T00:00:00.000Z",
        "updateTime": "2024-01-01T00:00:00.000Z",
        "labels": {
            "cloudidentity.googleapis.com/groups.discussion_forum": "",
        },
    },
    {
        "name": "groups/group-operations",
        "groupKey": {
            "id": "operations@simpson.corp",
        },
        "parent": "customers/ABC123CD",
        "displayName": "Operations",
        "description": "Operations sub-team",
        "createTime": "2023-02-01T00:00:00.000Z",
        "updateTime": "2024-02-01T00:00:00.000Z",
        "labels": {
            "cloudidentity.googleapis.com/groups.discussion_forum": "",
        },
    },
]


# See: https://cloud.google.com/identity/docs/reference/rest/v1/groups.memberships
MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL = {
    "groups/group-engineering": [
        {
            "name": "groups/group-engineering/memberships/member-1",
            "preferredMemberKey": {
                "id": "mbsimpson@simpson.corp",
            },
            "roles": [
                {
                    "name": "MEMBER",
                }
            ],
            "type": "USER",
            "createTime": "2023-01-01T00:00:00.000Z",
            "updateTime": "2024-01-01T00:00:00.000Z",
        },
        {
            "name": "groups/group-engineering/memberships/member-2",
            "preferredMemberKey": {
                "id": "hjsimpson@simpson.corp",
            },
            "roles": [
                {
                    "name": "MEMBER",
                }
            ],
            "type": "USER",
            "createTime": "2023-01-01T00:00:00.000Z",
            "updateTime": "2024-01-01T00:00:00.000Z",
        },
        {
            "name": "groups/group-engineering/memberships/member-3",
            "preferredMemberKey": {
                "id": "operations@simpson.corp",
            },
            "roles": [
                {
                    "name": "MEMBER",
                }
            ],
            "type": "GROUP",
            "createTime": "2023-01-01T00:00:00.000Z",
            "updateTime": "2024-01-01T00:00:00.000Z",
        },
    ],
    "groups/group-operations": [
        {
            "name": "groups/group-operations/memberships/member-1",
            "preferredMemberKey": {
                "id": "hjsimpson@simpson.corp",
            },
            "roles": [
                {
                    "name": "MEMBER",
                }
            ],
            "type": "USER",
            "createTime": "2023-02-01T00:00:00.000Z",
            "updateTime": "2024-02-01T00:00:00.000Z",
        },
    ],
}


# Mock OAuth tokens responses
# See: https://developers.google.com/workspace/admin/directory/reference/rest/v1/tokens/list
MOCK_GOOGLEWORKSPACE_OAUTH_TOKENS_BY_USER = {
    "user-1": [
        {
            "kind": "admin#directory#token",
            "etag": "etag-token-1",
            "clientId": "123456789.apps.googleusercontent.com",
            "displayText": "Slack",
            "anonymous": False,
            "nativeApp": False,
            "scopes": [
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        },
        {
            "kind": "admin#directory#token",
            "etag": "etag-token-2",
            "clientId": "987654321.apps.googleusercontent.com",
            "displayText": "Google Calendar Mobile",
            "anonymous": False,
            "nativeApp": True,
            "scopes": [
                "https://www.googleapis.com/auth/calendar",
            ],
        },
    ],
    "user-2": [
        {
            "kind": "admin#directory#token",
            "etag": "etag-token-3",
            "clientId": "123456789.apps.googleusercontent.com",
            "displayText": "Slack",
            "anonymous": False,
            "nativeApp": False,
            "scopes": [
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        },
    ],
}
