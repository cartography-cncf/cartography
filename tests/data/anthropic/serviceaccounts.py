ANTHROPIC_SERVICE_ACCOUNTS = [
    {
        "id": "svac_01Nb5RtYuIoPaSdFgHjKlZxC",
        "type": "service_account",
        "name": "reactor-telemetry",
        "description": "Collects reactor telemetry from the plant floor.",
        "organization_role": "developer",
        "created_at": "2025-01-10T09:00:00.000000Z",
        "updated_at": "2025-01-12T09:00:00.000000Z",
        "archived_at": None,
    },
    {
        "id": "svac_01Pq8WeRtYuIoPaSdFgHjKlM",
        "type": "service_account",
        "name": "cartography-collector",
        "description": "Read-only org:admin collector.",
        "organization_role": "admin",
        "created_at": "2025-02-01T10:30:00.000000Z",
        "updated_at": "2025-02-01T10:30:00.000000Z",
        "archived_at": None,
    },
]

# Keyed by service account id, as returned by
# GET /organizations/service_accounts/{id}/workspaces
ANTHROPIC_SERVICE_ACCOUNT_WORKSPACES = {
    "svac_01Nb5RtYuIoPaSdFgHjKlZxC": [
        {
            "type": "service_account_workspace_member",
            "service_account_id": "svac_01Nb5RtYuIoPaSdFgHjKlZxC",
            "workspace_id": "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ",
            "workspace_role": "workspace_developer",
            "implicit": False,
            "created_by_actor_id": "user_EneequohSheesh3Ohtaefu8we2aite",
        },
    ],
    "svac_01Pq8WeRtYuIoPaSdFgHjKlM": [
        {
            "type": "service_account_workspace_member",
            "service_account_id": "svac_01Pq8WeRtYuIoPaSdFgHjKlM",
            "workspace_id": "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ",
            "workspace_role": "workspace_admin",
            "implicit": False,
            "created_by_actor_id": "user_EneequohSheesh3Ohtaefu8we2aite",
        },
    ],
}
