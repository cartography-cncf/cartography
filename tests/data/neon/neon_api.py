"""
Mock Neon API payloads, shaped like the live responses of the v2 API.
"""

ORG_ID = "org-springfield-12345678"

ORGANIZATIONS = {
    "organizations": [
        {
            "id": ORG_ID,
            "name": "Springfield Nuclear",
            "handle": "springfield-nuclear-org-springfield-12345678",
            "plan": "scale",
            "created_at": "2025-01-01T09:00:00Z",
            "managed_by": "console",
            "updated_at": "2026-07-01T09:00:00Z",
            "require_mfa": False,
        },
    ],
}

ORGANIZATION = ORGANIZATIONS["organizations"][0]

HOMER_USER_ID = "8024488a-0000-4000-a000-000000000001"
BURNS_USER_ID = "8024488a-0000-4000-a000-000000000002"

# Two pages, to exercise cursor pagination.
MEMBERS_PAGE_1 = {
    "members": [
        {
            "member": {
                "id": "mem-burns",
                "user_id": BURNS_USER_ID,
                "org_id": ORG_ID,
                "role": "admin",
                "joined_at": "2025-01-01T09:00:00Z",
            },
            "user": {"email": "mburns@example.com", "has_mfa": True},
        },
    ],
    "pagination": {"next": "cursor-page-2", "sort_by": "joined_at"},
}

MEMBERS_PAGE_2 = {
    "members": [
        {
            "member": {
                "id": "mem-homer",
                "user_id": HOMER_USER_ID,
                "org_id": ORG_ID,
                "role": "member",
                "joined_at": "2025-02-01T09:00:00Z",
            },
            "user": {
                "email": "hsimpson@example.com",
                "has_mfa": False,
                "deactivated_at": "2026-01-01T00:00:00Z",
            },
        },
    ],
    "pagination": {"sort_by": "joined_at"},
}

PLANT_PROJECT_ID = "nuclear-plant-11111111"
GRID_PROJECT_ID = "power-grid-22222222"

API_KEYS = [
    {
        "id": 3422296,
        "name": "ci-deploy",
        "created_at": "2026-10-12T07:39:26Z",
        "created_by": {"id": BURNS_USER_ID, "name": "Monty Burns", "image": ""},
        "last_used_at": "2026-11-05T10:20:11Z",
        "last_used_from_addr": "198.51.100.7",
    },
    {
        "id": 3416601,
        "name": "plant-only",
        "created_at": "2026-10-10T07:25:49Z",
        "created_by": {"id": HOMER_USER_ID, "name": "Homer Simpson", "image": ""},
        "last_used_at": None,
        "last_used_from_addr": "",
        "project_id": PLANT_PROJECT_ID,
    },
]


def _project(project_id, name, settings):
    return {
        "id": project_id,
        "platform_id": "aws",
        "region_id": "aws-us-east-2",
        "name": name,
        "provisioner": "k8s-neonvm",
        "settings": settings,
        "pg_version": 17,
        "proxy_host": "c-9.us-east-2.aws.neon.tech",
        "branch_logical_size_limit": 0,
        "branch_logical_size_limit_bytes": -1,
        "store_passwords": True,
        "active_time": 0,
        "cpu_used_sec": 0,
        "creation_source": "console",
        "created_at": "2026-11-05T10:25:24Z",
        "updated_at": "2026-11-05T10:26:09Z",
        "owner_id": BURNS_USER_ID,
        "org_id": ORG_ID,
        "history_retention_seconds": 86400,
    }


# The plant locks down protected branches only. Its preview branch is not
# protected, so it stays reachable from anywhere.
PLANT_PROJECT = _project(
    PLANT_PROJECT_ID,
    "nuclear-plant",
    {
        "allowed_ips": {
            "ips": ["203.0.113.0/24"],
            "protected_branches_only": True,
        },
        "enable_logical_replication": False,
        "block_public_connections": False,
        "block_vpc_connections": False,
        "hipaa": False,
    },
)

GRID_PROJECT = _project(
    GRID_PROJECT_ID,
    "power-grid",
    {
        "enable_logical_replication": True,
        "block_public_connections": False,
    },
)

PROJECTS = {
    "projects": [PLANT_PROJECT, GRID_PROJECT],
    "pagination": {"cursor": GRID_PROJECT_ID},
}

PLANT_MAIN = "br-plant-main"
PLANT_PREVIEW = "br-plant-preview"
PLANT_HOTFIX = "br-plant-hotfix"
GRID_MAIN = "br-grid-main"


def _branch(branch_id, project_id, name, parent_id=None, protected=False):
    branch = {
        "id": branch_id,
        "project_id": project_id,
        "name": name,
        "current_state": "ready",
        "state_changed_at": "2026-11-05T10:25:26Z",
        "creation_source": "console",
        "primary": parent_id is None,
        "default": parent_id is None,
        "protected": protected,
        "cpu_used_sec": 0,
        "compute_time_seconds": 0,
        "active_time_seconds": 0,
        "written_data_bytes": 0,
        "data_transfer_bytes": 0,
        "created_at": "2026-11-05T10:25:24Z",
        "updated_at": "2026-11-05T10:26:09Z",
        "init_source": "parent-data",
    }
    if parent_id:
        branch["parent_id"] = parent_id
        branch["parent_timestamp"] = "2026-11-05T10:25:27Z"
    return branch


# Listed newest first, as the API does by default: children before parents.
PLANT_BRANCHES = {
    "branches": [
        _branch(PLANT_HOTFIX, PLANT_PROJECT_ID, "hotfix", parent_id=PLANT_PREVIEW),
        _branch(PLANT_PREVIEW, PLANT_PROJECT_ID, "preview", parent_id=PLANT_MAIN),
        _branch(PLANT_MAIN, PLANT_PROJECT_ID, "main", protected=True),
    ],
    "annotations": {},
    "pagination": {"sort_by": "updated_at", "sort_order": "DESC"},
}

GRID_BRANCHES = {
    "branches": [_branch(GRID_MAIN, GRID_PROJECT_ID, "main")],
    "annotations": {},
    "pagination": {"sort_by": "updated_at", "sort_order": "DESC"},
}


def _endpoint(endpoint_id, project_id, branch_id, disabled=False):
    host = f"{endpoint_id}.c-9.us-east-2.aws.neon.tech"
    return {
        "host": host,
        "hosts": {
            "read_write_host": host,
            "read_write_pooled_host": f"{endpoint_id}-pooler.c-9.us-east-2.aws.neon.tech",
        },
        "id": endpoint_id,
        "project_id": project_id,
        "branch_id": branch_id,
        "autoscaling_limit_min_cu": 0.25,
        "autoscaling_limit_max_cu": 2,
        "region_id": "aws-us-east-2",
        "type": "read_write",
        "current_state": "idle",
        "settings": {"pg_settings": {}},
        "pooler_enabled": False,
        "pooler_mode": "transaction",
        "disabled": disabled,
        "passwordless_access": True,
        "creation_source": "console",
        "created_at": "2026-11-05T10:25:24Z",
        "updated_at": "2026-11-05T10:26:00Z",
        "proxy_host": "c-9.us-east-2.aws.neon.tech",
        "suspend_timeout_seconds": 0,
        "provisioner": "k8s-neonvm",
    }


PLANT_ENDPOINTS = {
    "endpoints": [
        _endpoint("ep-plant-main", PLANT_PROJECT_ID, PLANT_MAIN),
        _endpoint("ep-plant-preview", PLANT_PROJECT_ID, PLANT_PREVIEW),
        _endpoint("ep-plant-hotfix", PLANT_PROJECT_ID, PLANT_HOTFIX, disabled=True),
    ],
}

GRID_ENDPOINTS = {
    "endpoints": [_endpoint("ep-grid-main", GRID_PROJECT_ID, GRID_MAIN)],
}

# The listing may carry a role password. It must never reach the graph.
LEAKED_PASSWORD = "npg_do-not-store-me"


def roles_for(branch_id):
    return {
        "roles": [
            {
                "branch_id": branch_id,
                "name": "neondb_owner",
                "password": LEAKED_PASSWORD,
                "protected": False,
                "authentication_method": "password",
                "created_at": "2026-11-05T10:25:24Z",
                "updated_at": "2026-11-05T10:25:24Z",
            },
        ],
    }


def databases_for(branch_id):
    return {
        "databases": [
            {
                "id": sum(map(ord, branch_id)),
                "branch_id": branch_id,
                "name": "neondb",
                "owner_name": "neondb_owner",
                "created_at": "2026-11-05T10:25:24Z",
                "updated_at": "2026-11-05T10:25:24Z",
            },
        ],
    }


# Buckets branch with the database, so every plant branch lists both.
PLANT_BUCKETS = {
    "buckets": [
        {
            "name": "reactor-telemetry",
            "access_level": "private",
            "created_at": "2026-11-05T10:25:35Z",
        },
        {
            "name": "press-kit",
            "access_level": "public_read",
            "created_at": "2026-11-05T10:25:34Z",
        },
    ],
}

EMPTY_BUCKETS: dict[str, list] = {"buckets": []}


def storage_for(branch_id):
    return {
        "enabled": True,
        "s3_endpoint": f"https://{branch_id}.storage.c-9.us-east-2.aws.neon.tech",
        "region": "us-east-2",
        "force_path_style": True,
    }


# A credential issued on main shows up on every descendant with main's branch_id.
PLANT_MAIN_CREDENTIAL = {
    "token_id": "nak_live_plant_main_rw",
    "token_id_short": "plantmainrw0",
    "name": "Default object storage credential",
    "scopes": ["storage:read", "storage:write"],
    "branch_id": PLANT_MAIN,
    "principal_type": "user",
    "created_at": "2026-11-05T10:25:25Z",
}

PLANT_PREVIEW_CREDENTIAL = {
    "token_id": "nak_live_plant_preview_ro",
    "token_id_short": "plantprevro0",
    "name": "preview reader",
    "scopes": ["storage:read"],
    "branch_id": PLANT_PREVIEW,
    "principal_type": "user",
    "created_at": "2026-11-05T10:26:25Z",
    "expires_at": "2027-01-01T00:00:00Z",
}

PLANT_MAIN_CREDENTIALS = {"credentials": [PLANT_MAIN_CREDENTIAL]}
PLANT_DESCENDANT_CREDENTIALS = {
    "credentials": [PLANT_MAIN_CREDENTIAL, PLANT_PREVIEW_CREDENTIAL],
}
EMPTY_CREDENTIALS: dict[str, list] = {"credentials": []}
