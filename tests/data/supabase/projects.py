SUPABASE_PROJECTS = [
    {
        "id": "nuclearplantdbaaaaaa",
        "ref": "nuclearplantdbaaaaaa",
        "organization_id": "abcdefghijklmnopqrst",
        "organization_slug": "simpson-corp",
        "name": "nuclear-plant",
        "region": "us-east-2",
        "status": "ACTIVE_HEALTHY",
        "created_at": "2026-07-01T10:00:00.000000Z",
        "database": {
            "host": "db.nuclearplantdbaaaaaa.supabase.co",
            "version": "17.6.1.147",
            "postgres_engine": "17",
            "release_channel": "ga",
        },
    },
    {
        "id": "kwikemartdbbbbbbbbbb",
        "ref": "kwikemartdbbbbbbbbbb",
        "organization_id": "abcdefghijklmnopqrst",
        "organization_slug": "simpson-corp",
        "name": "kwik-e-mart",
        "region": "eu-west-1",
        "status": "INACTIVE",
        "created_at": "2026-07-02T11:30:00.000000Z",
        "database": {
            "host": "db.kwikemartdbbbbbbbbbb.supabase.co",
            "version": "15.8.1.020",
            "postgres_engine": "15",
            "release_channel": "ga",
        },
    },
    # Belongs to a different organization, so it must not be picked up when
    # syncing simpson-corp.
    {
        "id": "monoraildbcccccccccc",
        "ref": "monoraildbcccccccccc",
        "organization_id": "tsrqponmlkjihgfedcba",
        "organization_slug": "burns-industries",
        "name": "monorail",
        "region": "us-west-1",
        "status": "ACTIVE_HEALTHY",
        "created_at": "2026-07-03T09:15:00.000000Z",
        "database": {
            "host": "db.monoraildbcccccccccc.supabase.co",
            "version": "17.6.1.147",
            "postgres_engine": "17",
            "release_channel": "ga",
        },
    },
]

# GET /v1/projects/{ref}/api-keys/legacy
SUPABASE_LEGACY_API_KEYS = {"enabled": True}

# GET /v1/projects/{ref}/postgrest. `jwt_secret` is present here on purpose: the
# transform must drop it.
SUPABASE_POSTGREST_CONFIG = {
    "db_schema": "public, graphql_public",
    "max_rows": 1000,
    "db_extra_search_path": "public, extensions",
    "db_pool": None,
    "db_pool_acquisition_timeout": 10,
    "jwt_secret": "super-secret-jwt-value-that-must-never-be-ingested",
}

# GET /v1/projects/{ref}/config/storage
SUPABASE_STORAGE_CONFIG = {
    "fileSizeLimit": 52428800,
    "features": {
        "imageTransformation": {"enabled": True},
        "s3Protocol": {"enabled": True},
        "purgeCache": {"enabled": False},
    },
}

# GET /v1/projects/{ref}/config/realtime
SUPABASE_REALTIME_CONFIG = {
    "private_only": False,
    "connection_pool": 5,
    "max_concurrent_users": 200,
    "presence_enabled": True,
}

# GET /v1/projects/{ref}/vanity-subdomain
SUPABASE_VANITY_SUBDOMAIN = {
    "status": "active",
    "custom_domain": "nuclear-plant.supabase.co",
}

# GET /v1/projects/{ref}/ssl-enforcement
SUPABASE_SSL_ENFORCEMENT = {
    "currentConfig": {"database": True},
    "appliedSuccessfully": True,
}

# GET /v1/projects/{ref}/network-restrictions
SUPABASE_NETWORK_RESTRICTIONS = {
    "entitlement": "allowed",
    "config": {
        "dbAllowedCidrs": ["10.0.0.0/8"],
        "dbAllowedCidrsV6": ["2600:1f18::/48"],
    },
    "old_config": None,
    "status": "applied",
    "updated_at": "2026-07-10T08:00:00Z",
    "applied_at": "2026-07-10T08:01:00Z",
}

# GET /v1/projects/{ref}/database/backups
SUPABASE_DATABASE_BACKUPS = {
    "region": "us-east-2",
    "walg_enabled": True,
    "pitr_enabled": False,
    "backups": [
        {
            "id": 1,
            "is_physical_backup": True,
            "status": "COMPLETED",
            "inserted_at": "2026-07-25T02:00:00Z",
        },
        {
            "id": 2,
            "is_physical_backup": True,
            "status": "COMPLETED",
            "inserted_at": "2026-07-26T02:00:00Z",
        },
    ],
}


# GET /v1/organizations/{slug}/projects. This is the authority for which projects an
# organization has. Note the different shape from /v1/projects: `inserted_at` rather
# than `created_at`, no `organization_slug`, and a `databases` array that carries no
# host or version. `sharedprojectdddddddd` is deliberately absent from
# SUPABASE_PROJECTS above, standing in for a project created by another member of the
# organization: /v1/projects would not return it.
SUPABASE_ORG_PROJECTS = {
    "projects": [
        {
            "ref": "nuclearplantdbaaaaaa",
            "name": "nuclear-plant",
            "cloud_provider": "AWS",
            "region": "us-east-2",
            "is_branch": False,
            "status": "ACTIVE_HEALTHY",
            "inserted_at": "2026-07-01T10:00:00.000000Z",
            "databases": [
                {
                    "identifier": "nuclearplantdbaaaaaa",
                    "type": "PRIMARY",
                    "region": "us-east-2",
                    "status": "ACTIVE_HEALTHY",
                    "cloud_provider": "AWS",
                    "infra_compute_size": "nano",
                },
            ],
        },
        {
            "ref": "kwikemartdbbbbbbbbbb",
            "name": "kwik-e-mart",
            "cloud_provider": "AWS",
            "region": "eu-west-1",
            "is_branch": False,
            "status": "INACTIVE",
            "inserted_at": "2026-07-02T11:30:00.000000Z",
            "databases": [],
        },
        {
            "ref": "sharedprojectdddddddd",
            "name": "shared-by-a-colleague",
            "cloud_provider": "AWS",
            "region": "us-west-1",
            "is_branch": False,
            "status": "ACTIVE_HEALTHY",
            "inserted_at": "2026-07-04T08:00:00.000000Z",
            "databases": [],
        },
    ],
    "pagination": {"offset": 0, "limit": 100, "count": 3},
}
