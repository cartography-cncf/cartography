CLOUD_ID = "11111111-1111-4111-8111-111111111111"
OTHER_CLOUD_ID = "22222222-2222-4222-8222-222222222222"

USERS = [
    {
        "accountId": "user-1",
        "displayName": "Example User",
        "emailAddress": "user@example.com",
        "active": True,
        "accountType": "atlassian",
    },
    {
        "accountId": "user-2",
        "displayName": "Private User",
        "active": False,
        "accountType": "atlassian",
    },
]
GROUPS = [
    {"groupId": "group-1", "name": "Engineering"},
    {"groupId": "group-2", "name": "Site Managers"},
]
PROJECTS = [
    {
        "id": "100",
        "key": "EX",
        "name": "Example",
        "style": "classic",
        "projectTypeKey": "software",
        "lead": USERS[0],
    },
    {
        "id": "200",
        "key": "TEAM",
        "name": "Example Team",
        "style": "next-gen",
        "projectTypeKey": "software",
    },
]
ROLE = {
    "id": 10,
    "name": "Developers",
    "admin": False,
    "actors": [
        {"type": "atlassian-user-role-actor", "actorUser": {"accountId": "user-1"}},
        {"type": "atlassian-group-role-actor", "actorGroup": {"groupId": "group-1"}},
    ],
}
SCHEME = {
    "id": 500,
    "name": "Example permissions",
    "permissions": [
        {
            "id": 1,
            "permission": "BROWSE_PROJECTS",
            "holder": {"type": "projectRole", "parameter": "10"},
        },
        {
            "id": 2,
            "permission": "ADMINISTER_PROJECTS",
            "holder": {
                "type": "group",
                "value": "group-2",
                "parameter": "Site Managers",
            },
        },
        {
            "id": 3,
            "permission": "EDIT_ISSUES",
            "holder": {"type": "user", "parameter": "user-1"},
        },
        {"id": 4, "permission": "BROWSE_PROJECTS", "holder": {"type": "anyone"}},
    ],
}
API_RESPONSES = {
    "mypermissions": {
        "permissions": {
            "ADMINISTER": {"havePermission": True},
            "BROWSE_USERS": {"havePermission": True},
        }
    },
    "serverInfo": {
        "deploymentType": "Cloud",
        "serverTitle": "Example",
        "baseUrl": "https://example.atlassian.net",
    },
    "project/100/roledetails": [{"id": 10}],
    "project/100/role/10": ROLE,
    "project/200/roledetails": [{"id": 10}],
    "project/200/role/10": {
        "id": 10,
        "name": "Administrator",
        "admin": True,
        "actors": [],
    },
    "project/100/permissionscheme": {"id": 500},
    "permissionscheme/500": SCHEME,
}
