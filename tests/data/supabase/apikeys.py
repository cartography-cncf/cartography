# GET /v1/projects/{ref}/api-keys. Called without ?reveal, so `api_key` is absent
# from every entry: the key material never reaches Cartography.
SUPABASE_API_KEYS = [
    {
        "id": "key-publishable-1",
        "type": "publishable",
        "prefix": "sb_publishable_",
        "name": "default publishable",
        "description": "Browser-safe key",
        "hash": "hash-publishable-1",
        "secret_jwt_template": None,
        "inserted_at": "2026-07-01T10:05:00Z",
        "updated_at": "2026-07-01T10:05:00Z",
    },
    {
        "id": "key-secret-1",
        "type": "secret",
        "prefix": "sb_secret_",
        "name": "server key",
        "description": None,
        "hash": "hash-secret-1",
        "secret_jwt_template": None,
        "inserted_at": "2026-07-01T10:06:00Z",
        "updated_at": "2026-07-02T12:00:00Z",
    },
    # Legacy anon / service_role keys predate per-key ids, so `id` is null and the
    # transform must synthesise one from the project ref plus type.
    {
        "id": None,
        "type": "legacy",
        "prefix": None,
        "name": "anon",
        "description": None,
        "hash": None,
        "secret_jwt_template": None,
        "inserted_at": None,
        "updated_at": None,
    },
]

# GET /v1/projects/{ref}/config/auth/signing-keys
SUPABASE_SIGNING_KEYS = {
    "keys": [
        {
            "id": "signing-key-current",
            "algorithm": "ES256",
            "status": "in_use",
            "public_jwk": {"kty": "EC", "crv": "P-256"},
            "created_at": "2026-07-01T10:00:00Z",
            "updated_at": "2026-07-01T10:00:00Z",
        },
        {
            "id": "signing-key-standby",
            "algorithm": "ES256",
            "status": "standby",
            "public_jwk": {"kty": "EC", "crv": "P-256"},
            "created_at": "2026-07-15T10:00:00Z",
            "updated_at": "2026-07-15T10:00:00Z",
        },
    ],
}
