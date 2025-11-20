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
