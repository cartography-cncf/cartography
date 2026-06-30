from datetime import datetime

from dateutil.tz import tzutc
from scaleway.domain.v2beta1 import DNSZone
from scaleway.domain.v2beta1 import Record

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

TEST_ZONE_DOMAIN = "example-cartography.com"
TEST_ZONE_ID = TEST_ZONE_DOMAIN  # apex zone -> id = domain

TEST_RECORD_A_ID = "11111111-aaaa-4820-b8d6-0eef10cfcd6d"
TEST_RECORD_MX_ID = "22222222-bbbb-4820-b8d6-0eef10cfcd6d"


SCALEWAY_DNS_ZONES = [
    DNSZone(
        domain=TEST_ZONE_DOMAIN,
        subdomain="",
        ns=["ns0.dom.scw.cloud", "ns1.dom.scw.cloud"],
        ns_default=["ns0.dom.scw.cloud", "ns1.dom.scw.cloud"],
        ns_master=[],
        status="active",
        project_id=TEST_PROJECT_ID,
        linked_products=[],
        message="",
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]

SCALEWAY_DNS_RECORDS_BY_ZONE = {
    TEST_ZONE_DOMAIN: [
        Record(
            data="1.2.3.4",
            name="www",
            priority=0,
            ttl=3600,
            type_="a",
            id=TEST_RECORD_A_ID,
            comment="",
            updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        ),
        Record(
            data="mail.example-cartography.com.",
            name="",
            priority=10,
            ttl=3600,
            type_="mx",
            id=TEST_RECORD_MX_ID,
            comment="primary mx",
            updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        ),
    ],
}
