PROJECTS_RESPONSE = {
    "list": {
        "objects": [
            {
                "uuid": "proj-001",
                "meta": {
                    "name": "acme/frontend-app",
                    "description": "Frontend application",
                    "create_time": "2024-01-15T10:00:00Z",
                    "update_time": "2024-06-01T12:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "platform_source": "PLATFORM_SOURCE_GITHUB",
                    "git": {
                        "http_clone_url": "https://github.com/acme/frontend-app.git",
                    },
                },
                "processing_status": {
                    "scan_state": "SCAN_STATE_IDLE",
                },
            },
            {
                "uuid": "proj-002",
                "meta": {
                    "name": "acme/backend-api",
                    "description": "Backend API service",
                    "create_time": "2024-02-01T08:00:00Z",
                    "update_time": "2024-06-10T14:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "platform_source": "PLATFORM_SOURCE_GITHUB",
                    "git": {
                        "http_clone_url": "https://github.com/acme/backend-api.git",
                    },
                },
                "processing_status": {
                    "scan_state": "SCAN_STATE_IDLE",
                },
            },
        ],
        "response": {
            "next_page_token": None,
        },
    },
}
