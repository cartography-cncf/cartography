from datetime import datetime

from dateutil.tz import tzutc
from scaleway.account.v3 import Project

SCALEWAY_PROJECTS = [
    Project(
        id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        name="default",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        description="",
        created_at=datetime(2025, 3, 20, 7, 39, 54, 220004, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 7, 39, 54, 220004, tzinfo=tzutc()),
    )
]
