from datetime import datetime

from dateutil.tz import tzutc
from scaleway.vpcgw.v2 import Gateway
from scaleway.vpcgw.v2 import GatewayNetwork
from scaleway.vpcgw.v2 import GatewayNetworkStatus
from scaleway.vpcgw.v2 import GatewayStatus
from scaleway.vpcgw.v2 import IP
from scaleway.vpcgw.v2 import PatRule
from scaleway.vpcgw.v2 import PatRuleProtocol

from tests.data.scaleway.network import TEST_PRIVATE_NETWORK_ID

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_GATEWAY_ID = "aaaaaaaa-9999-4820-b8d6-0eef10cfcd6d"
TEST_GATEWAY_IP_ID = "bbbbbbbb-9999-4820-b8d6-0eef10cfcd6d"
TEST_PAT_RULE_ID = "cccccccc-9999-4820-b8d6-0eef10cfcd6d"
TEST_GATEWAY_NETWORK_ID = "dddddddd-9999-4820-b8d6-0eef10cfcd6d"

_TS = datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc())


SCALEWAY_PUBLIC_GATEWAYS = [
    Gateway(
        id=TEST_GATEWAY_ID,
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        type_="VPC-GW-S",
        bandwidth=100,
        status=GatewayStatus.RUNNING,
        name="demo-gateway",
        tags=["demo"],
        gateway_networks=[
            GatewayNetwork(
                id=TEST_GATEWAY_NETWORK_ID,
                gateway_id=TEST_GATEWAY_ID,
                private_network_id=TEST_PRIVATE_NETWORK_ID,
                masquerade_enabled=True,
                status=GatewayNetworkStatus.READY,
                push_default_route=True,
                ipam_ip_id=None,
                zone="fr-par-1",
                created_at=_TS,
                updated_at=_TS,
                mac_address=None,
            )
        ],
        bastion_enabled=True,
        bastion_port=61000,
        smtp_enabled=False,
        is_legacy=False,
        bastion_allowed_ips=["0.0.0.0/0"],
        zone="fr-par-1",
        created_at=_TS,
        updated_at=_TS,
        ipv4=IP(
            id=TEST_GATEWAY_IP_ID,
            organization_id=TEST_ORG_ID,
            project_id=TEST_PROJECT_ID,
            tags=[],
            address="51.15.1.1",
            zone="fr-par-1",
            created_at=_TS,
            updated_at=_TS,
            reverse=None,
            gateway_id=TEST_GATEWAY_ID,
        ),
        version="2",
        can_upgrade_to=None,
    )
]


SCALEWAY_PAT_RULES = [
    PatRule(
        id=TEST_PAT_RULE_ID,
        gateway_id=TEST_GATEWAY_ID,
        public_port=2222,
        private_ip="192.168.1.10",
        private_port=22,
        protocol=PatRuleProtocol.TCP,
        zone="fr-par-1",
        created_at=_TS,
        updated_at=_TS,
    )
]
