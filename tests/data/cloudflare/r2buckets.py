CLOUDFLARE_R2_BUCKETS = [
    {
        "name": "donut-photos",
        "creation_date": "2024-02-11T09:12:33.000Z",
        "location": "wnam",
        "jurisdiction": "default",
        "storage_class": "Standard",
    },
    {
        "name": "nuclear-safety-reports",
        "creation_date": "2024-05-02T18:45:07.000Z",
        "location": "enam",
        "jurisdiction": "default",
        "storage_class": "InfrequentAccess",
    },
]

# Keyed by bucket name, as returned by r2.buckets.domains.managed.list().
CLOUDFLARE_R2_MANAGED_DOMAINS = {
    "donut-photos": {
        "bucketId": "3f8b1c2d4e5a6b7c8d9e0f1a2b3c4d5e",
        "domain": "pub-3f8b1c2d4e5a6b7c8d9e0f1a2b3c4d5e.r2.dev",
        "enabled": True,
    },
    "nuclear-safety-reports": {
        "bucketId": "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d",
        "domain": "pub-9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d.r2.dev",
        "enabled": False,
    },
}

# Keyed by bucket name, as returned by r2.buckets.domains.custom.list().
CLOUDFLARE_R2_CUSTOM_DOMAINS = {
    "donut-photos": [
        {
            "domain": "photos.simpson.corp",
            "enabled": True,
            "status": {"ownership": "active", "ssl": "active"},
            "zoneId": "be68b067-5b2b-49f7-ad89-943d501dc900",
            "zoneName": "simpson.corp",
            "minTLS": "1.2",
        },
        {
            "domain": "old-photos.simpson.corp",
            "enabled": False,
            "status": {"ownership": "active", "ssl": "active"},
            "zoneId": "be68b067-5b2b-49f7-ad89-943d501dc900",
            "zoneName": "simpson.corp",
            "minTLS": "1.2",
        },
    ],
    "nuclear-safety-reports": [],
}
