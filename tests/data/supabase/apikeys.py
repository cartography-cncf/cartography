# GET /v1/projects/{ref}/api-keys. Shaped after the live API: despite `reveal`
# being omitted, the endpoint returns the full `api_key` value for every key type,
# including the service_role secret. The values below are dummies and must be
# dropped in transform, never reaching the graph.
SUPABASE_API_KEYS = [
    {
        "api_key": "sb_publishable_dummy_value_that_must_be_dropped",
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
        "api_key": "sb_secret_dummy_value_that_must_be_dropped",
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
    # The spec marks `id` nullable, so cover the fallback path where the transform
    # synthesises an id from the project ref plus type. The live API does return
    # "anon" / "service_role" ids for legacy keys, covered by the entry below.
    {
        "api_key": "eyJhbGciOiJIUzI1NiJ9.dummy-legacy-jwt-that-must-be-dropped",
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
    {
        "api_key": "eyJhbGciOiJIUzI1NiJ9.dummy-service-role-jwt-must-be-dropped",
        "id": "service_role",
        "type": "legacy",
        "prefix": "A3KdY",
        "name": "service_role",
        "description": None,
        "hash": "hash-service-role",
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
