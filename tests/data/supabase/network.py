# GET /v1/projects/{ref}/config/database/pooler. The connection strings are present
# on purpose: they embed credentials and the transform must drop them.
SUPABASE_POOLERS = [
    {
        "identifier": "nuclearplantdbaaaaaa",
        "database_type": "PRIMARY",
        "is_using_scram_auth": True,
        "db_user": "postgres",
        "db_host": "aws-0-us-east-2.pooler.supabase.com",
        "db_port": 6543,
        "db_name": "postgres",
        "connection_string": "postgres://postgres:hunter2@aws-0-us-east-2.pooler.supabase.com:6543/postgres",
        "connectionString": "postgres://postgres:hunter2@aws-0-us-east-2.pooler.supabase.com:6543/postgres",
        "default_pool_size": 15,
        "max_client_conn": 200,
        "pool_mode": "transaction",
    },
]

# GET /v1/projects/{ref}/custom-hostname
SUPABASE_CUSTOM_HOSTNAME = {
    "status": "3_challenge_verified",
    "custom_hostname": "api.simpson.corp",
    "data": {
        "success": True,
        "errors": [],
        "messages": [],
        "result": {
            "id": "cf-hostname-1",
            "hostname": "api.simpson.corp",
            "ssl": {
                "status": "active",
                "validation_records": [],
                "validation_errors": [],
            },
            "ownership_verification": {
                "type": "txt",
                "name": "_cf-custom-hostname.api.simpson.corp",
                "value": "verification-token",
            },
            "custom_origin_server": "nuclearplantdbaaaaaa.supabase.co",
            "verification_errors": [],
            "status": "active",
        },
    },
}

# The endpoint answers 200 with an empty config when no custom hostname is set up.
SUPABASE_CUSTOM_HOSTNAME_UNSET = {
    "status": "0_not_started",
    "custom_hostname": None,
    "data": None,
}
