ORG_ID = "00000000-0000-4000-8000-000000000001"
ORG_STALE_ID = "00000000-0000-4000-8000-000000000101"
TARGET_ID = "00000000-0000-4000-8000-000000000002"
PROJECT_ID = "00000000-0000-4000-8000-000000000003"
ISSUE_CVE_ID = "00000000-0000-4000-8000-000000000004"
ISSUE_ADVISORY_ID = "00000000-0000-4000-8000-000000000005"

ORG = {
    "id": ORG_ID,
    "type": "org",
    "attributes": {
        "name": "Example Org",
        "slug": "example-org",
        "group_id": "00000000-0000-4000-8000-000000000099",
    },
}

ORG_STALE = {
    "id": ORG_STALE_ID,
    "type": "org",
    "attributes": {
        "name": "Stale Org",
        "slug": "stale-org",
        "group_id": "00000000-0000-4000-8000-000000000199",
    },
}

TARGETS = [
    {
        "id": TARGET_ID,
        "type": "target",
        "attributes": {
            "display_name": "example/app",
            "url": "https://github.com/example/app",
            "origin": "github",
        },
    },
]

PROJECTS = [
    {
        "id": PROJECT_ID,
        "type": "project",
        "attributes": {
            "name": "example/app:Dockerfile",
            "type": "dockerfile",
            "origin": "github",
            "target_reference": "main",
            "created": "2026-01-01T00:00:00Z",
        },
        "relationships": {
            "target": {"data": {"id": TARGET_ID, "type": "target"}},
        },
    },
]

ISSUES = [
    {
        "id": ISSUE_CVE_ID,
        "type": "issue",
        "attributes": {
            "title": "Prototype Pollution in minimist",
            "identifiers": {"CVE": ["CVE-2021-44906"], "CWE": ["CWE-1321"]},
            "effective_severity_level": "high",
            "status": "open",
            "ignored": False,
            "cvss_score": 9.8,
            "exploit_maturity": "mature",
            "package_name": "minimist",
            "package_version": "0.0.8",
            "is_upgradable": True,
            "created_at": "2026-01-02T00:00:00Z",
            "updated_at": "2026-01-03T00:00:00Z",
            "description": "A vulnerable package was found.",
        },
        "relationships": {
            "scan_item": {"data": {"id": PROJECT_ID, "type": "project"}},
        },
    },
    {
        "id": ISSUE_ADVISORY_ID,
        "type": "issue",
        "attributes": {
            "title": "License policy issue",
            "identifiers": {"SNYK": ["SNYK-JS-EXAMPLE-123"]},
            "effective_severity_level": "medium",
            "status": "open",
            "ignored": True,
            "package_name": "example",
            "package_version": "1.0.0",
            "is_upgradable": False,
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-05T00:00:00Z",
        },
        "relationships": {
            "scan_item": {"data": {"id": PROJECT_ID, "type": "project"}},
        },
    },
]

ORG_COLLECTION_PAGE_1 = {
    "data": [{"id": "one", "type": "target", "attributes": {"display_name": "one"}}],
    "links": {"next": "/rest/orgs/example/targets?starting_after=cursor-1"},
}

ORG_COLLECTION_PAGE_2 = {
    "data": [{"id": "two", "type": "target", "attributes": {"display_name": "two"}}],
    "links": {},
}
