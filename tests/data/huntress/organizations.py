"""Huntress API v1 `Organization` responses."""

from typing import Any

ORGANIZATIONS: list[dict[str, Any]] = [
    {
        "id": 2001,
        "agents_count": 2,
        "account_id": 1000,
        "created_at": "2026-01-05T09:14:22Z",
        "incident_reports_count": 2,
        "key": "springfield",
        "logs_sources_count": 0,
        "microsoft_365_tenant_id": None,
        "microsoft_365_users_count": 0,
        "identity_provider_tenant_id": "d7ae1d1e-9c0f-4b0a-9d21-1f6f2c2b7a10",
        "billable_identity_count": 4,
        "name": "Springfield Elementary",
        "notify_emails": [],
        "report_recipients": ["skinner@springfield.example.com"],
        "sat_learner_count": 0,
        "updated_at": "2026-02-11T18:02:41Z",
    },
    {
        "id": 2002,
        "agents_count": 1,
        "account_id": 1000,
        "created_at": "2026-01-06T11:47:03Z",
        "incident_reports_count": 1,
        "key": "shelbyville",
        "logs_sources_count": 0,
        "microsoft_365_tenant_id": None,
        "microsoft_365_users_count": 0,
        "identity_provider_tenant_id": None,
        "billable_identity_count": 0,
        "name": "Shelbyville Elementary",
        "notify_emails": [],
        "report_recipients": [],
        "sat_learner_count": 0,
        "updated_at": "2026-02-09T07:33:15Z",
    },
]
