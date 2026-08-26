from cartography.intel.notion.scim import ENTERPRISE_USER_EXTENSION
from cartography.intel.notion.scim import NOTION_USER_EXTENSION

SCIM_USERS = [
    {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": "person-1",
        "externalId": "employee-alice",
        "userName": "ALICE@example.com",
        "name": {
            "formatted": "Alice Example",
            "givenName": "Alice",
            "familyName": "Example",
        },
        "active": True,
        "title": "Security Engineer",
        "userType": "Employee",
        "locale": "en-US",
        "preferredLanguage": "en",
        ENTERPRISE_USER_EXTENSION: {
            "department": "Security",
            "division": "Engineering",
            "costCenter": "CC-42",
            "organization": "Example Corp",
            "employeeNumber": "E-1",
        },
        NOTION_USER_EXTENSION: {"role": "owner"},
    },
    {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": "person-2",
        "externalId": "employee-bob",
        "userName": "bob@example.com",
        "name": {"givenName": "Bob", "familyName": "Example"},
        "active": True,
        ENTERPRISE_USER_EXTENSION: {
            "manager": {
                "value": "ALICE@example.com",
                "displayName": "Alice Example",
            },
        },
        NOTION_USER_EXTENSION: {"role": "member"},
    },
]

SCIM_GROUPS = [
    {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "id": "group-1",
        "externalId": "security-team",
        "displayName": "Security",
        "members": [
            {"value": "person-1", "display": "Alice Example"},
            {"value": "person-2", "display": "Bob Example"},
        ],
    },
]
