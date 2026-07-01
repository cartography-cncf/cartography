from datetime import datetime

from dateutil.tz import tzutc
from scaleway.applesilicon.v1alpha1 import Server as AppleSiliconServer
from scaleway.baremetal.v1 import IP as BaremetalIP
from scaleway.baremetal.v1 import Server as ElasticMetalServer
from scaleway.dedibox.v1 import IP as DediboxIP
from scaleway.dedibox.v1 import NetworkInterface
from scaleway.dedibox.v1 import ServerSummary as DediboxServer
from scaleway.flexibleip.v1alpha1 import FlexibleIP as ElasticMetalFlexibleIP

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

SCALEWAY_ELASTIC_METAL_SERVERS = [
    ElasticMetalServer(
        id="11111111-1111-1111-1111-111111111111",
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        name="em-demo",
        description="demo elastic metal",
        status="ready",
        offer_id="offer-em-a115x",
        offer_name="EM-A115X-SSD",
        tags=["demo"],
        ips=[
            BaremetalIP(
                id="ip-1",
                address="51.15.1.1",
                reverse="em-demo.example.com",
                version="IPv4",
                reverse_status="active",
                reverse_status_message="",
            ),
        ],
        domain="em-demo.example.com",
        boot_type="normal",
        zone="fr-par-1",
        ping_status="ping_status_up",
        options=[],
        protected=False,
        created_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
    ),
]

SCALEWAY_APPLE_SILICON_SERVERS = [
    AppleSiliconServer(
        id="22222222-2222-2222-2222-222222222222",
        type_="M2-M",
        name="mac-demo",
        project_id=TEST_PROJECT_ID,
        organization_id=TEST_ORG_ID,
        ip="51.15.2.2",
        vnc_url="",
        ssh_username="m1",
        sudo_password="",
        vnc_port=5900,
        status="ready",
        deletion_scheduled=False,
        zone="fr-par-1",
        delivered=True,
        vpc_status="disabled",
        public_bandwidth_bps=1000000000,
        tags=["demo"],
        applied_runner_configuration_ids=[],
        created_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
    ),
]

SCALEWAY_DEDIBOX_SERVERS = [
    DediboxServer(
        id=12345,
        datacenter_name="DC5",
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        hostname="dedibox-demo",
        offer_id=678,
        offer_name="Start-1-M-SATA",
        status="active",
        interfaces=[
            NetworkInterface(
                card_id=1,
                device_id=2,
                mac="de:ad:be:ef:00:01",
                type_="public",
                ips=[
                    DediboxIP(
                        ip_id=9001,
                        address="163.172.3.3",
                        reverse="dedibox-demo.example.com",
                        version="IPv4",
                        cidr=32,
                        netmask="255.255.255.255",
                        semantic="main",
                        gateway="163.172.3.1",
                        status="active",
                    ),
                ],
            ),
        ],
        zone="fr-par-1",
        is_outsourced=False,
        qinq=False,
        is_hds=False,
        created_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
    ),
]

SCALEWAY_ELASTIC_METAL_FLEXIBLE_IPS = [
    ElasticMetalFlexibleIP(
        id="fip00000-0000-0000-0000-000000000001",
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        description="em flexible ip",
        tags=["demo"],
        status="attached",
        ip_address="51.15.9.9",
        reverse="em-demo.example.com",
        zone="fr-par-1",
        server_id="11111111-1111-1111-1111-111111111111",
        created_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
    ),
]
