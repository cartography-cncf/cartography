DEPENDENCY_METADATA_RESPONSE = {
    "list": {
        "objects": [
            {
                "uuid": "dep-001",
                "meta": {
                    "name": "npm://lodash@4.17.21",
                    "parent_uuid": "pkg-002",
                    "create_time": "2024-03-01T10:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "importer_data": {
                        "project_uuid": "proj-001",
                    },
                    "dependency_data": {
                        "direct": True,
                        "reachable": True,
                        "scope": "SCOPE_RUNTIME",
                        "package_version_uuid": "pkg-001",
                    },
                },
            },
            {
                "uuid": "dep-002",
                "meta": {
                    "name": "npm://qs@6.11.0",
                    "parent_uuid": "pkg-002",
                    "create_time": "2024-03-01T10:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "importer_data": {
                        "project_uuid": "proj-001",
                    },
                    "dependency_data": {
                        "direct": False,
                        "reachable": False,
                        "scope": "SCOPE_RUNTIME",
                        "package_version_uuid": None,
                    },
                },
            },
        ],
        "response": {
            "next_page_token": None,
        },
    },
}
