# Buckets as returned by r2.buckets.list(), keyed by the jurisdiction the listing
# was scoped to. `donut-photos` exists in both the default and the EU
# jurisdiction: jurisdictions are separate namespaces, so the same account can
# hold two different buckets under one name.
CLOUDFLARE_R2_BUCKETS_BY_JURISDICTION: dict[str, list[dict]] = {
    "default": [
        {
            "name": "donut-photos",
            "creation_date": "2024-02-11T09:12:33.000Z",
            "location": "wnam",
            "storage_class": "Standard",
        },
        {
            "name": "nuclear-safety-reports",
            "creation_date": "2024-05-02T18:45:07.000Z",
            "location": "enam",
            "storage_class": "InfrequentAccess",
        },
    ],
    "eu": [
        {
            "name": "donut-photos",
            "creation_date": "2024-07-19T11:02:54.000Z",
            "location": "eeur",
            "jurisdiction": "eu",
            "storage_class": "Standard",
        },
    ],
    "fedramp": [],
}

# What get() returns: every jurisdiction's buckets, each carrying the jurisdiction
# it was listed in.
CLOUDFLARE_R2_BUCKETS = [
    {**bucket, "jurisdiction": jurisdiction}
    for jurisdiction, buckets in CLOUDFLARE_R2_BUCKETS_BY_JURISDICTION.items()
    for bucket in buckets
]

# Keyed by (jurisdiction, bucket name), as returned by
# r2.buckets.domains.managed.list().
CLOUDFLARE_R2_MANAGED_DOMAINS = {
    ("default", "donut-photos"): {
        "bucketId": "3f8b1c2d4e5a6b7c8d9e0f1a2b3c4d5e",
        "domain": "pub-3f8b1c2d4e5a6b7c8d9e0f1a2b3c4d5e.r2.dev",
        "enabled": True,
    },
    ("default", "nuclear-safety-reports"): {
        "bucketId": "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d",
        "domain": "pub-9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d.r2.dev",
        "enabled": False,
    },
    ("eu", "donut-photos"): {
        "bucketId": "1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e",
        "domain": "pub-1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e.r2.dev",
        "enabled": False,
    },
}

# Keyed by (jurisdiction, bucket name), as returned by
# r2.buckets.domains.custom.list().
CLOUDFLARE_R2_CUSTOM_DOMAINS: dict[tuple[str, str], list[dict]] = {
    ("default", "donut-photos"): [
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
    ("default", "nuclear-safety-reports"): [],
    ("eu", "donut-photos"): [],
}
