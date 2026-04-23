PACKAGE_VERSIONS_RESPONSE = {
    "list": {
        "objects": [
            {
                "uuid": "pkg-001",
                "meta": {
                    "name": "npm://lodash@4.17.21",
                    "parent_uuid": "proj-001",
                    "create_time": "2024-03-01T10:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "project_uuid": "proj-001",
                    "ecosystem": "ECOSYSTEM_NPM",
                    "release_timestamp": "2021-02-20T00:00:00Z",
                    "call_graph_available": True,
                },
            },
            {
                "uuid": "pkg-002",
                "meta": {
                    "name": "npm://express@4.18.2",
                    "parent_uuid": "proj-001",
                    "create_time": "2024-03-01T10:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "project_uuid": "proj-001",
                    "ecosystem": "ECOSYSTEM_NPM",
                    "release_timestamp": "2023-10-12T00:00:00Z",
                    "call_graph_available": False,
                },
            },
            {
                "uuid": "pkg-003",
                "meta": {
                    "name": "pypi://requests@2.31.0",
                    "parent_uuid": "proj-002",
                    "create_time": "2024-04-01T10:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "project_uuid": "proj-002",
                    "ecosystem": "ECOSYSTEM_PYPI",
                    "release_timestamp": "2023-05-22T00:00:00Z",
                    "call_graph_available": False,
                },
            },
        ],
        "response": {
            "next_page_token": None,
        },
    },
}
