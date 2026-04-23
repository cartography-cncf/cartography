FINDINGS_RESPONSE = {
    "list": {
        "objects": [
            {
                "uuid": "finding-001",
                "meta": {
                    "name": "lodash-prototype-pollution",
                    "create_time": "2024-05-01T12:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "project_uuid": "proj-001",
                    "summary": "Prototype pollution vulnerability in lodash",
                    "level": "FINDING_LEVEL_CRITICAL",
                    "finding_categories": [
                        "FINDING_CATEGORY_VULNERABILITY",
                    ],
                    "finding_tags": [
                        "FINDING_TAGS_REACHABLE_FUNCTION",
                        "FINDING_TAGS_FIX_AVAILABLE",
                    ],
                    "target_dependency_name": "lodash",
                    "target_dependency_version": "4.17.21",
                    "target_dependency_package_name": "npm://lodash@4.17.21",
                    "proposed_version": "4.17.22",
                    "remediation": "Upgrade lodash to version 4.17.22 or later",
                    "remediation_action": "REMEDIATION_ACTION_UPGRADE",
                    "target_uuid": "dep-001",
                    "finding_metadata": {
                        "vulnerability": {
                            "aliases": ["CVE-2024-0001", "GHSA-xxxx-yyyy-zzzz"],
                            "cvss_base_score": 9.8,
                            "spec_version": "3.1",
                        },
                    },
                },
            },
            {
                "uuid": "finding-002",
                "meta": {
                    "name": "outdated-express-release",
                    "create_time": "2024-05-15T09:00:00Z",
                },
                "tenant_meta": {
                    "namespace": "acme-corp",
                },
                "spec": {
                    "project_uuid": "proj-001",
                    "summary": "Outdated release of express detected",
                    "level": "FINDING_LEVEL_MEDIUM",
                    "finding_categories": [
                        "FINDING_CATEGORY_SUPPLY_CHAIN",
                    ],
                    "finding_tags": [
                        "FINDING_TAGS_FIX_AVAILABLE",
                    ],
                    "target_dependency_name": "express",
                    "target_dependency_version": "4.18.2",
                    "target_dependency_package_name": "npm://express@4.18.2",
                    "proposed_version": "4.19.0",
                    "remediation": "Upgrade express to version 4.19.0 or later",
                    "remediation_action": "REMEDIATION_ACTION_UPGRADE",
                    "target_uuid": None,
                    "finding_metadata": {},
                },
            },
        ],
        "response": {
            "next_page_token": None,
        },
    },
}
