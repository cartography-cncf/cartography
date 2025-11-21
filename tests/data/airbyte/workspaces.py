AIRBYTE_WORKSPACES = [
    {
        "workspaceId": "e4388e31-9c21-461b-9b5d-1905ca28c599",
        "name": "SpringField Nuclear Plant",
        "dataResidency": "us",
        "notifications": {
            "failure": {"email": {"enabled": True}, "webhook": {"enabled": False}},
            "success": {"email": {"enabled": False}, "webhook": {"enabled": False}},
            "connectionUpdate": {
                "email": {"enabled": True},
                "webhook": {"enabled": False},
            },
            "connectionUpdateActionRequired": {
                "email": {"enabled": True},
                "webhook": {"enabled": False},
            },
            "syncDisabled": {"email": {"enabled": True}, "webhook": {"enabled": False}},
            "syncDisabledWarning": {
                "email": {"enabled": True},
                "webhook": {"enabled": False},
            },
        },
    }
]
