"""Shapes returned by the storage, key-value and network adapter helpers.

Field values mirror responses captured from a real Modal workspace on modal 1.5.3, except for
domains and proxies: those RPCs returned nothing on the test workspace (custom domains are a
paid add-on), so their shapes come from the protobuf definitions.
"""

from datetime import datetime
from datetime import timezone

# cartography.intel.modal.util.list_secrets()
MODAL_SECRETS = [
    {
        "id": "st-poEHPwc7kwkkLwrnaVPjTn",
        "name": "e2e-secret",
        "created_at": datetime(2026, 7, 29, 21, 37, 37, tzinfo=timezone.utc),
        # Never read by any workload.
        "last_used_at": None,
        # A workspace username, not an email: this is what CREATED_BY joins on.
        "created_by": "alice",
    },
    {
        "id": "st-2XbNmQwErTyUiOpAsDfGh",
        "name": "prod-db-password",
        "created_at": datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc),
        "last_used_at": datetime(2026, 7, 30, 5, 0, 0, tzinfo=timezone.utc),
        # No member has this display name, so no CREATED_BY edge must appear.
        "created_by": "someone-who-left",
    },
]

# cartography.intel.modal.util.list_volumes()
MODAL_VOLUMES = [
    {
        "id": "vo-Fq2DSfh5sU2E9kQ6R9oDrj",
        "name": "e2e-volume",
        "created_at": datetime(2026, 7, 29, 21, 37, 38, tzinfo=timezone.utc),
        "created_by": "alice",
        "version": "VOLUME_FS_VERSION_V1",
    },
    {
        "id": "vo-9ZxCvBnMqWeRtYuIoPaSdF",
        "name": "model-weights",
        "created_at": datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc),
        "created_by": "bob",
        "version": "VOLUME_FS_VERSION_V2",
    },
]

# cartography.intel.modal.util.list_nfs()
MODAL_NETWORK_FILE_SYSTEMS = [
    {
        "id": "sv-1AsDfGhJkLzXcVbNmQwErT",
        "name": "legacy-share",
        "created_at": datetime(2026, 1, 10, 8, 0, 0, tzinfo=timezone.utc),
        "cloud_provider": "CLOUD_PROVIDER_AWS",
    },
]

# cartography.intel.modal.util.list_dicts()
MODAL_DICTS = [
    {
        "id": "di-F91whmwZVRH92mOiJgNOCT",
        "name": "e2e-dict",
        "created_at": datetime(2026, 7, 29, 21, 37, 39, tzinfo=timezone.utc),
    },
]

# cartography.intel.modal.util.list_queues()
MODAL_QUEUES = [
    {
        "id": "qu-kbM1N097wnpOSJgRjiwXvk",
        "name": "e2e-queue",
        "created_at": datetime(2026, 7, 29, 21, 37, 39, tzinfo=timezone.utc),
        # Modal leaves these at 0 for an empty queue; the adapter maps 0 to None.
        "num_partitions": None,
        "total_size": None,
    },
]

# cartography.intel.modal.util.list_domains()
MODAL_DOMAINS = [
    {
        "id": "dm-5TgBnHyUjMkIoLpQaZwSxE",
        "domain_name": "api.example.com",
        "created_at": datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
        "certificate_status": "CERTIFICATE_STATUS_ISSUED",
        "dns_records": [
            {
                "type": "DNS_RECORD_TYPE_CNAME",
                "name": "api.example.com",
                "value": "cname.modal.host",
            },
            {
                "type": "DNS_RECORD_TYPE_TXT",
                "name": "_modal-challenge.api.example.com",
                "value": "verify-token-abc",
            },
        ],
    },
    {
        # A domain whose certificate never issued is serving without valid TLS.
        "id": "dm-6YhNjUmIkOlPaQsWdEfRgT",
        "domain_name": "broken.example.com",
        "created_at": datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc),
        "certificate_status": "CERTIFICATE_STATUS_FAILED",
        "dns_records": [],
    },
]

# cartography.intel.modal.util.list_proxies()
MODAL_PROXIES = [
    {
        "id": "pr-7YhNjUmIkOlPaQsWdEfRgT",
        "name": "egress-proxy",
        "created_at": datetime(2026, 7, 5, 11, 0, 0, tzinfo=timezone.utc),
        "region": "us-east-1",
        "environment_name": "main",
        "proxy_ips": [
            {
                "ip_address": "203.0.113.10",
                "status": "PROXY_IP_STATUS_ONLINE",
                "created_at": datetime(2026, 7, 5, 11, 0, 5, tzinfo=timezone.utc),
            },
            {
                "ip_address": "203.0.113.11",
                "status": "PROXY_IP_STATUS_UNHEALTHY",
                "created_at": datetime(2026, 7, 5, 11, 0, 6, tzinfo=timezone.utc),
            },
        ],
    },
    {
        # Belongs to a different environment, so the per-environment sync must filter it out.
        "id": "pr-8ZiOkVnJmLpQaZwSxEdCrF",
        "name": "other-env-proxy",
        "created_at": datetime(2026, 7, 6, 11, 0, 0, tzinfo=timezone.utc),
        "region": "eu-west-1",
        "environment_name": "prod",
        "proxy_ips": [
            {
                "ip_address": "203.0.113.20",
                "status": "PROXY_IP_STATUS_ONLINE",
                "created_at": datetime(2026, 7, 6, 11, 0, 5, tzinfo=timezone.utc),
            },
        ],
    },
]
