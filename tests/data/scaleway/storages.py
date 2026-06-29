from datetime import datetime

from dateutil.tz import tzutc
from scaleway.instance.v1 import ServerSummary
from scaleway.instance.v1 import Snapshot
from scaleway.instance.v1 import SnapshotBaseVolume
from scaleway.instance.v1 import Volume

SCALEWAY_VOLUMES = [
    Volume(
        id="7c37b328-247c-4668-8ee1-701a3a3cc2e4",
        name="Ubuntu 24.04 Noble Numbat",
        size=20000000000,
        volume_type="l_ssd",
        organization="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        creation_date=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        modification_date=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        tags=[],
        state="available",
        zone="fr-par-1",
        server=ServerSummary(
            id="345627e9-18ff-47e0-b73d-3f38fddb4390", name="demo-server"
        ),
    )
]

SCALEWAY_SNAPSHOTS = [
    Snapshot(
        id="7c689d68-94a7-4498-9a87-d83077859519",
        name="image-gateway_snap_0",
        organization="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        tags=[],
        volume_type="l_ssd",
        size=20000000000,
        state="available",
        zone="fr-par-1",
        base_volume=SnapshotBaseVolume(
            id="7c37b328-247c-4668-8ee1-701a3a3cc2e4", name="Ubuntu 24.04 Noble Numbat"
        ),
        creation_date=datetime(2025, 6, 20, 12, 29, 45, 284101, tzinfo=tzutc()),
        modification_date=datetime(2025, 6, 20, 12, 30, 29, 573322, tzinfo=tzutc()),
        error_reason=None,
    )
]

# Object Storage buckets are S3-compatible: get() returns raw boto3-shaped dicts.
# get() tags each bucket with the project it was enumerated under.
_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
_OWNER_ID = f"{_PROJECT_ID}:{_PROJECT_ID}"

SCALEWAY_BUCKETS = [
    {
        "name": "cartography-private-bucket",
        "region": "fr-par",
        "endpoint": "https://cartography-private-bucket.s3.fr-par.scw.cloud",
        "creation_date": datetime(2025, 6, 20, 12, 0, 0, tzinfo=tzutc()),
        "project_id": _PROJECT_ID,
        "acl": {
            "Owner": {"ID": _OWNER_ID, "DisplayName": _OWNER_ID},
            "Grants": [
                {
                    "Grantee": {"ID": _OWNER_ID, "Type": "CanonicalUser"},
                    "Permission": "FULL_CONTROL",
                }
            ],
        },
        "policy": None,
        "versioning": {"Status": "Enabled"},
        "tags": {
            "TagSet": [
                {"Key": "env", "Value": "test"},
                {"Key": "owner", "Value": "cartography"},
            ]
        },
    },
    {
        "name": "cartography-public-bucket",
        "region": "nl-ams",
        "endpoint": "https://cartography-public-bucket.s3.nl-ams.scw.cloud",
        "creation_date": datetime(2025, 6, 20, 12, 5, 0, tzinfo=tzutc()),
        "project_id": _PROJECT_ID,
        "acl": {
            "Owner": {"ID": _OWNER_ID, "DisplayName": _OWNER_ID},
            "Grants": [
                {
                    "Grantee": {
                        "Type": "Group",
                        "URI": "http://acs.amazonaws.com/groups/global/AllUsers",
                    },
                    "Permission": "READ",
                }
            ],
        },
        "policy": {
            "Policy": (
                '{"Version":"2023-04-17","Statement":[{"Sid":"AllowPublicRead",'
                '"Effect":"Allow","Principal":"*","Action":"s3:GetObject",'
                '"Resource":"cartography-public-bucket/*"}]}'
            )
        },
        "versioning": None,
        "tags": None,
    },
]
