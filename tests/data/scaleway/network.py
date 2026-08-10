from datetime import datetime

from dateutil.tz import tzutc
from scaleway.ipam.v1 import IP
from scaleway.ipam.v1 import Resource
from scaleway.ipam.v1 import Source
from scaleway.vpc.v2 import PrivateNetwork
from scaleway.vpc.v2 import Subnet
from scaleway.vpc.v2 import VPC

TEST_VPC_ID = "11111111-1111-4820-b8d6-0eef10cfcd6d"
TEST_PRIVATE_NETWORK_ID = "22222222-2222-4820-b8d6-0eef10cfcd6d"
TEST_SUBNET_ID = "33333333-3333-4820-b8d6-0eef10cfcd6d"
TEST_IP_ID = "44444444-4444-4820-b8d6-0eef10cfcd6d"

SCALEWAY_VPCS = [
    VPC(
        id=TEST_VPC_ID,
        name="demo-vpc",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        region="fr-par",
        tags=["demo"],
        is_default=True,
        private_network_count=1,
        routing_enabled=True,
        custom_routes_propagation_enabled=False,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]

SCALEWAY_PRIVATE_NETWORKS = [
    PrivateNetwork(
        id=TEST_PRIVATE_NETWORK_ID,
        name="demo-pn",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        region="fr-par",
        tags=["demo"],
        vpc_id=TEST_VPC_ID,
        dhcp_enabled=True,
        default_route_propagation_enabled=True,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        subnets=[
            Subnet(
                id=TEST_SUBNET_ID,
                subnet="172.16.8.0/22",
                project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
                private_network_id=TEST_PRIVATE_NETWORK_ID,
                vpc_id=TEST_VPC_ID,
                created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
                updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
            ),
        ],
    )
]

SCALEWAY_IPS = [
    IP(
        id=TEST_IP_ID,
        address="172.16.8.2/22",
        project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        is_ipv6=False,
        tags=["demo"],
        reverses=[],
        region="fr-par",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        source=Source(subnet_id=TEST_SUBNET_ID),
        resource=Resource(
            type_="instance_private_nic",
            id="55555555-5555-4820-b8d6-0eef10cfcd6d",
            mac_address="02:00:00:00:00:01",
            name="demo-server",
        ),
        zone=None,
    )
]
