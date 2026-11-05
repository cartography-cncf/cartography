from tests.data.langsmith.organizations import LANGSMITH_ORG_ID

WORKSPACE_PROD_ID = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa"
WORKSPACE_DEV_ID = "bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb"

LANGSMITH_WORKSPACES = [
    {
        "id": WORKSPACE_PROD_ID,
        "organization_id": LANGSMITH_ORG_ID,
        "display_name": "Production",
        "tenant_handle": "production",
        "is_personal": False,
        "is_deleted": False,
        "data_plane_url": None,
        "created_at": "2026-01-04T10:00:00Z",
    },
    {
        "id": WORKSPACE_DEV_ID,
        "organization_id": LANGSMITH_ORG_ID,
        "display_name": "Development",
        "tenant_handle": "development",
        "is_personal": False,
        "is_deleted": False,
        "data_plane_url": None,
        "created_at": "2026-01-05T10:00:00Z",
    },
]
