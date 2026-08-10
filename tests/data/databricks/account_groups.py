DATABRICKS_ACCOUNT_GROUPS = [
    {
        "id": "310001",
        "displayName": "account users",
        "externalId": None,
    },
    {
        "id": "310002",
        "displayName": "admins",
        "externalId": "grp-admins",
        # Nested group: admins is a member of "account users".
        "groups": [
            {"value": "310001", "display": "account users"},
        ],
    },
]
