SUPABASE_ORGANIZATIONS = [
    {
        "id": "abcdefghijklmnopqrst",
        "slug": "simpson-corp",
        "name": "Simpson Corp",
    },
    {
        "id": "tsrqponmlkjihgfedcba",
        "slug": "burns-industries",
        "name": "Burns Industries",
    },
]

# Keyed by slug, which is how GET /v1/organizations/{slug} is addressed.
SUPABASE_ORGANIZATION_DETAILS = {
    "simpson-corp": {
        "id": "abcdefghijklmnopqrst",
        "name": "Simpson Corp",
        "plan": "pro",
        "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN"],
        "allowed_release_channels": ["ga", "preview"],
    },
    "burns-industries": {
        "id": "tsrqponmlkjihgfedcba",
        "name": "Burns Industries",
        "plan": "free",
        "opt_in_tags": [],
        "allowed_release_channels": ["ga"],
    },
}

SUPABASE_ORGANIZATION_MEMBERS = [
    {
        "user_id": "user-marge",
        "user_name": "mbsimpson",
        "email": "mbsimpson@simpson.corp",
        "role_name": "Owner",
        "mfa_enabled": True,
        "avatar_url": "https://example.com/marge.png",
    },
    {
        "user_id": "user-homer",
        "user_name": "hjsimpson",
        "email": "hjsimpson@simpson.corp",
        "role_name": "Developer",
        "mfa_enabled": False,
        "avatar_url": None,
    },
]
