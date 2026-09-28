"""
Netlify fixtures for the resources that could not be provisioned on a Free-plan team.

Hand-written from https://open-api.netlify.com/ rather than captured live:

- notification hooks: `createHookBySiteId` returns HTTP 422 through the Netlify CLI
- forms: form detection only runs during a Netlify build, and the e2e site was deployed prebuilt
- service instances (add-ons): none installable on the test team
- TLS certificates: provisioning needs a custom domain with delegated DNS
- database snapshots: none taken on the test database

Each payload deliberately keeps the credential-bearing fields Netlify really returns, so the
tests can assert that they never reach the graph. Ids match the other fixtures in this package.
"""

from typing import Any

NETLIFY_HOOKS: list[dict[str, Any]] = [
    {
        # `data` holds the Slack incoming-webhook URL, which must not be ingested.
        "created_at": "2026-07-30T16:19:42.220Z",
        # The token part is deliberately too short to look like a real Slack webhook: a
        # realistically shaped one trips GitHub's push protection on this very file. The host is
        # kept so the leak assertion in the tests still has something to match on.
        "data": {"url": "https://hooks.slack.com/services/TFIXTURE/BFIXTURE/nottoken"},
        "disabled": False,
        "event": "deploy_created",
        "id": "9e9e7d7053c60b4be4c87201",
        "site_id": "11111111-2222-3333-4444-555555555555",
        "type": "slack",
        "updated_at": "2026-07-30T16:19:42.220Z",
    },
    {
        "created_at": "2026-07-30T16:19:42.220Z",
        "data": {"url": "https://webhook.example.com/netlify?token=s3cr3t"},
        "disabled": True,
        "event": "deploy_failed",
        "id": "9e9e7d7053c60b4be4c87202",
        "site_id": "11111111-2222-3333-4444-555555555555",
        "type": "url",
        "updated_at": "2026-07-30T16:19:42.220Z",
    },
]

NETLIFY_FORMS: list[dict[str, Any]] = [
    {
        "created_at": "2026-07-30T16:19:23.884Z",
        "fields": [
            {"name": "name", "type": "text"},
            {"name": "email", "type": "email"},
        ],
        "id": "afaf7d7053c60b4be4c87301",
        "name": "contact",
        "paths": ["/index.html"],
        "site_id": "11111111-2222-3333-4444-555555555555",
        "submission_count": 12,
    },
]

NETLIFY_SERVICE_INSTANCES: list[dict[str, Any]] = [
    {
        # `config`, `env` and `auth_url` all carry provisioned credentials.
        "auth_url": "https://addon.example.com/sso?jwt=eyJhbGciOiJIUzI1NiJ9.payload.signature",
        "config": {"api_key": "addon-live-key-abcdef"},
        "created_at": "2026-07-30T16:19:23.884Z",
        "env": {"ADDON_TOKEN": "addon-live-token-123456"},
        "external_attributes": {"account": "acct_123"},
        "id": "b0b07d7053c60b4be4c87401",
        "service_name": "Example Analytics",
        "service_path": "/.netlify/analytics",
        "service_slug": "example-analytics",
        "snippets": [],
        "updated_at": "2026-07-30T16:19:23.884Z",
        "url": "https://analytics.example.com",
    },
]

NETLIFY_CERTIFICATE: dict[str, Any] = {
    "created_at": "2026-07-30T16:19:23.884Z",
    "domains": [
        "example-site.dev",
        "www.example-site.dev",
    ],
    "expires_at": "2026-10-28T16:19:23.884Z",
    "state": "issued",
    "updated_at": "2026-07-30T16:19:23.884Z",
}

NETLIFY_DATABASE_SNAPSHOTS: list[dict[str, Any]] = [
    {
        "created_at": "2026-07-30T18:00:00Z",
        "expires_at": "2026-08-06T18:00:00Z",
        "id": "c1c17d7053c60b4be4c87501",
        "manual": True,
        "source_branch_id": "production",
        "timestamp": "2026-07-30T17:59:00Z",
    },
]
