from datetime import datetime

from dateutil.tz import tzutc
from scaleway.webhosting.v1 import HostingSummary

TEST_HOSTING_ID = "11111111-1111-1111-1111-111111111111"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

SCALEWAY_WEBHOSTINGS = [
    HostingSummary(
        id=TEST_HOSTING_ID,
        project_id=TEST_PROJECT_ID,
        created_at=datetime(2026, 7, 10, 12, 0, 0, tzinfo=tzutc()),
        updated_at=datetime(2026, 7, 10, 12, 30, 0, tzinfo=tzutc()),
        status="ready",
        protected=True,
        offer_name="mini",
        region="fr-par",
        domain="example.com",
        dns_status="valid",
        domain_status="valid",
    ),
]
