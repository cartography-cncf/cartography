OPENAI_ADMINAPIKEYS = [
    {
        "object": "organization.admin_api_key",
        "id": "key_abc",
        "name": "Administration Key",
        "redacted_value": "sk-admin...def",
        "value": "sk-admin-1234abcd",
        "created_at": 1711471533,
        "last_used_at": 1711471534,
        "owner": {
            "type": "user",
            "object": "organization.user",
            "id": "user-uJeighaeFair8shaa2av",
            "name": "Marge Simpson",
            "created_at": 1711471533,
            "role": "owner",
        },
    },
    # This is a project-scoped key that the bugged admin endpoint returns
    # mislabeled as an admin key. It has the same ID as a project API key.
    {
        "object": "organization.admin_api_key",
        "id": "key_iegheiWieG2jupheeYin",
        "name": "Chaos Monkey Script",
        "redacted_value": "sk-admin...xyz",
        "value": "sk-admin-5678efgh",
        "created_at": 1743941100,
        "last_used_at": 1743941100,
        "owner": {
            "type": "service_account",
            "object": "organization.service_account",
            "id": "user-ohp0mahG0Aw5eevu6ain",
            "name": "Chaos Monkey",
            "created_at": 1743941100,
            "role": "member",
        },
    },
]
