ANTHROPIC_ENVIRONMENTS = [
    {
        "id": "env_01Kd7Rt2Nm5Bq8Vx3Wy6Pz9L",
        "type": "environment",
        "name": "locked-down",
        "description": "Allowlisted egress only.",
        "config": {
            "networking": {
                "type": "limited",
                "allowed_hosts": ["api.springfield.corp"],
                "allow_mcp_servers": True,
                "allow_package_managers": False,
            },
            "packages": {"pip": ["requests"]},
        },
        "scope": "organization",
        "archived_at": None,
        "created_at": "2025-06-01T09:00:00.000000Z",
        "updated_at": "2025-06-01T09:00:00.000000Z",
    },
    {
        "id": "env_02Wq4Jm9Zn6Rt1Cx8Bv5Hd3K",
        "type": "environment",
        "name": "wide-open",
        "description": "No egress restriction.",
        "config": {"networking": "unrestricted", "packages": {}},
        "scope": "account",
        "archived_at": None,
        "created_at": "2025-06-02T09:00:00.000000Z",
        "updated_at": "2025-06-02T09:00:00.000000Z",
    },
]

ANTHROPIC_VAULTS = [
    {
        "id": "vlt_01Tz6Nb3Kw8Qm2Xr5Jd9Pc4V",
        "type": "vault",
        "display_name": "plant-credentials",
        "archived_at": None,
        "created_at": "2025-06-03T09:00:00.000000Z",
        "updated_at": "2025-06-03T09:00:00.000000Z",
    },
]

ANTHROPIC_MEMORY_STORES = [
    {
        "id": "memstore_01Bd8Vq5Rk2Wn7Tj4Lm6Zx3C",
        "type": "memory_store",
        "name": "shift-handover",
        "description": "What the previous shift left running.",
        "archived_at": None,
        "created_at": "2025-06-04T09:00:00.000000Z",
        "updated_at": "2025-06-04T09:00:00.000000Z",
    },
]

ANTHROPIC_AGENTS = [
    {
        "id": "agent_01Rn5Wx9Kt3Bm7Qd2Vz8Lp6J",
        "type": "agent",
        "name": "reactor-monitor",
        "description": "Watches reactor telemetry and files incidents.",
        "system": "You watch the reactor.",
        "version": 3,
        "model": {"id": "claude-opus-5", "effort": "high", "speed": "standard"},
        "mcp_servers": [
            {"name": "telemetry", "type": "url", "url": "https://mcp.springfield.corp"},
        ],
        "skills": [
            {
                "skill_id": "skill_01Mv4Zq7Nr2Ks8Ld3Tp6Wx9B",
                "type": "skill",
                "version": "1738240000000000",
            },
        ],
        "tools": [
            {"name": "read_sensor", "permission_policy": "always_allow"},
            {"name": "scram_reactor", "permission_policy": "always_ask"},
        ],
        "metadata": {},
        "archived_at": None,
        "created_at": "2025-06-05T09:00:00.000000Z",
        "updated_at": "2025-06-06T09:00:00.000000Z",
    },
]

ANTHROPIC_DEPLOYMENTS = [
    {
        "id": "depl_01Ym2Qc7Jx4Nv9Rb5Kd8Tw3P",
        "type": "deployment",
        "agent": {"id": "agent_01Rn5Wx9Kt3Bm7Qd2Vz8Lp6J", "version": 3},
        "environment_id": "env_01Kd7Rt2Nm5Bq8Vx3Wy6Pz9L",
        "schedule": {
            "type": "cron",
            "expression": "0 * * * *",
            "timezone": "UTC",
            "last_run_at": "2025-06-10T09:00:00.000000Z",
            "upcoming_runs_at": ["2025-06-10T10:00:00.000000Z"],
        },
        "status": "active",
        "paused_reason": None,
        "vault_ids": ["vlt_01Tz6Nb3Kw8Qm2Xr5Jd9Pc4V"],
        "metadata": {},
        "created_at": "2025-06-07T09:00:00.000000Z",
        "updated_at": "2025-06-07T09:00:00.000000Z",
    },
]
