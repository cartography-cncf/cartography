"""
Netlify DNS fixtures.

Hand-written from https://open-api.netlify.com/ rather than captured live: creating a DNS zone
returns HTTP 500 on a Free-plan team, so this shape could not be observed against the real API
the way the rest of the Netlify fixtures were. Ids and domains are stable fakes matching the
other fixtures in this package.

The one exception is the domain registration object on the first zone's `domain`, which is
transcribed from a production traceback. The spec declares `domain` as a string and does not
describe that object at all, so the spec alone could not have produced it.
"""

from typing import Any

NETLIFY_DNS_ZONES: list[dict[str, Any]] = [
    {
        "account_id": "5f5a5d7053c60b4be4c8784d",
        "account_name": "Example Team",
        "account_slug": "example-team",
        "created_at": "2026-07-30T16:18:52.098Z",
        "dedicated": False,
        "dns_servers": [
            "dns1.p05.nsone.net",
            "dns2.p05.nsone.net",
        ],
        # A domain bought through Netlify: `domain` holds the whole domain registration object
        # instead of the string the spec documents. Its `id`, `name`, `created_at` and
        # `updated_at` deliberately differ from the zone's own, so a transform that spread the
        # object onto the zone would clobber them and fail the node assertions.
        "domain": {
            "account_id": "5f5a5d7053c60b4be4c8784d",
            "auth_code": "super-secret-epp-transfer-code",
            "auto_renew": True,
            "auto_renew_at": "2027-06-28T16:18:52.098Z",
            "created_at": "2025-07-30T16:18:52.098Z",
            "deleted": False,
            "expires_at": "2027-07-30T16:18:52.098Z",
            "failure_reason": None,
            "id": "6b6b6d7053c60b4be4c87301",
            "name": "example-site.dev",
            "registered_at": "2025-07-30T16:18:52.098Z",
            "renewal_price": "19.99",
            "status": "payment_succeeded",
            "transferred_at": None,
            "updated_at": "2026-07-01T03:00:05.303Z",
            "user_id": "5f5a5d7053c60b4be4c8784b",
        },
        "errors": [],
        "id": "7c7c7d7053c60b4be4c87001",
        "ipv6_enabled": True,
        "name": "example-site.dev",
        "records": [],
        "site_id": "11111111-2222-3333-4444-555555555555",
        "supported_record_types": [
            "A",
            "AAAA",
            "ALIAS",
            "CAA",
            "CNAME",
            "MX",
            "NS",
            "SPF",
            "SRV",
            "TXT",
        ],
        "updated_at": "2026-07-30T16:20:20.019Z",
        "user_id": "5f5a5d7053c60b4be4c8784b",
    },
    {
        # A zone held at team level, not attached to any site, and reporting a delegation
        # error: the dangling-delegation shape a rule would look for.
        "account_id": "5f5a5d7053c60b4be4c8784d",
        "account_name": "Example Team",
        "account_slug": "example-team",
        "created_at": "2026-07-30T16:18:52.098Z",
        "dedicated": False,
        "dns_servers": [
            "dns1.p05.nsone.net",
            "dns2.p05.nsone.net",
        ],
        # Registered elsewhere and merely delegated to Netlify DNS, so `domain` is the plain
        # string the spec documents: the other branch of the zone transform.
        "domain": "orphan.example",
        "errors": ["NS records for orphan.example do not point to Netlify DNS"],
        "id": "7c7c7d7053c60b4be4c87002",
        "ipv6_enabled": False,
        "name": "orphan.example",
        "records": [],
        "site_id": None,
        "supported_record_types": ["A", "AAAA", "CNAME", "MX", "TXT"],
        "updated_at": "2026-07-30T16:20:20.019Z",
        "user_id": "5f5a5d7053c60b4be4c8784b",
    },
]

NETLIFY_DNS_RECORDS: list[dict[str, Any]] = [
    {
        "dns_zone_id": "7c7c7d7053c60b4be4c87001",
        "flag": None,
        "hostname": "example-site.dev",
        "id": "8d8d7d7053c60b4be4c87101",
        "managed": True,
        "priority": None,
        "site_id": "11111111-2222-3333-4444-555555555555",
        "tag": None,
        "ttl": 3600,
        "type": "NETLIFY",
        "value": "example-site.netlify.app",
    },
    {
        # Set by hand rather than managed by Netlify, and pointing at a third party: the shape
        # a subdomain-takeover rule looks for.
        "dns_zone_id": "7c7c7d7053c60b4be4c87001",
        "flag": None,
        "hostname": "blog.example-site.dev",
        "id": "8d8d7d7053c60b4be4c87102",
        "managed": False,
        "priority": None,
        "site_id": None,
        "tag": None,
        "ttl": 300,
        "type": "CNAME",
        "value": "some-tenant.example-saas.com",
    },
    {
        "dns_zone_id": "7c7c7d7053c60b4be4c87002",
        "flag": 0,
        "hostname": "orphan.example",
        "id": "8d8d7d7053c60b4be4c87103",
        "managed": False,
        "priority": None,
        "site_id": None,
        "tag": "issue",
        "ttl": 3600,
        "type": "CAA",
        "value": "letsencrypt.org",
    },
]
