# GET /v1/projects/{ref}/functions. Note created_at / updated_at are epoch
# milliseconds here, unlike the ISO-8601 strings the rest of the API returns.
SUPABASE_EDGE_FUNCTIONS = [
    {
        "id": "fn-meltdown-alert",
        "slug": "meltdown-alert",
        "name": "meltdown-alert",
        "status": "ACTIVE",
        "version": 3,
        "created_at": 1782000000000,
        "updated_at": 1782600000000,
        "verify_jwt": True,
        "import_map": True,
        "entrypoint_path": "./functions/meltdown-alert/index.ts",
        "import_map_path": "./functions/meltdown-alert/deno.json",
        "ezbr_sha256": "a" * 64,
    },
    # verify_jwt False means this one is publicly invokable.
    {
        "id": "fn-public-webhook",
        "slug": "public-webhook",
        "name": "public-webhook",
        "status": "ACTIVE",
        "version": 1,
        "created_at": 1782100000000,
        "updated_at": 1782100000000,
        "verify_jwt": False,
        "import_map": False,
        "entrypoint_path": "./functions/public-webhook/index.ts",
        "import_map_path": None,
        "ezbr_sha256": "b" * 64,
    },
]

# GET /v1/projects/{ref}/secrets. `value` is present on purpose: the transform must
# drop it so no secret material lands in the graph.
SUPABASE_SECRETS = [
    {
        "name": "SENTRY_DSN",
        "value": "https://public@sentry.example.com/1",
        "updated_at": "2026-07-20T09:00:00Z",
    },
    {
        "name": "PLANT_CONTROL_TOKEN",
        "value": "do-not-ingest-this-value",
        "updated_at": "2026-07-21T14:30:00Z",
    },
]
