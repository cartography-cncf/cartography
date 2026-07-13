from datetime import datetime

from dateutil.tz import tzutc
from scaleway.lb.v1 import Backend
from scaleway.lb.v1 import Frontend
from scaleway.lb.v1 import HealthCheck
from scaleway.lb.v1 import Ip
from scaleway.lb.v1 import Lb

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_LB_ID = "aaaa1111-1111-4820-b8d6-0eef10cfcd6d"
TEST_FRONTEND_ID = "bbbb2222-2222-4820-b8d6-0eef10cfcd6d"
TEST_BACKEND_ID = "cccc3333-3333-4820-b8d6-0eef10cfcd6d"

_LB_SUMMARY = Lb(
    id=TEST_LB_ID,
    name="demo-lb",
    description="Demo load balancer",
    status="ready",
    instances=[],
    organization_id=TEST_ORG_ID,
    project_id=TEST_PROJECT_ID,
    ip=[],
    tags=["demo"],
    frontend_count=1,
    backend_count=1,
    type_="LB-S",
    ssl_compatibility_level="ssl_compatibility_level_intermediate",
    private_network_count=0,
    route_count=0,
    zone="fr-par-1",
)

SCALEWAY_LOADBALANCERS = [
    Lb(
        id=TEST_LB_ID,
        name="demo-lb",
        description="Demo load balancer",
        status="ready",
        instances=[],
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        ip=[
            Ip(
                id="dddd4444-4444-4820-b8d6-0eef10cfcd6d",
                ip_address="51.159.0.1",
                organization_id=TEST_ORG_ID,
                project_id=TEST_PROJECT_ID,
                reverse="",
                tags=["demo"],
                zone="fr-par-1",
                lb_id=TEST_LB_ID,
                region="fr-par",
            )
        ],
        tags=["demo"],
        frontend_count=1,
        backend_count=1,
        type_="LB-S",
        ssl_compatibility_level="ssl_compatibility_level_intermediate",
        private_network_count=0,
        route_count=0,
        zone="fr-par-1",
        region="fr-par",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]

SCALEWAY_LB_BACKENDS = [
    Backend(
        id=TEST_BACKEND_ID,
        name="demo-backend",
        forward_protocol="tcp",
        forward_port=80,
        forward_port_algorithm="roundrobin",
        sticky_sessions="none",
        sticky_sessions_cookie_name="",
        pool=["172.16.16.5", "172.16.16.6"],
        on_marked_down_action="on_marked_down_action_none",
        proxy_protocol="proxy_protocol_none",
        health_check=HealthCheck(
            port=80,
            check_max_retries=3,
            check_send_proxy=False,
        ),
        lb=_LB_SUMMARY,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]

SCALEWAY_LB_FRONTENDS = [
    Frontend(
        id=TEST_FRONTEND_ID,
        name="demo-frontend",
        inbound_port=80,
        certificate_ids=[],
        enable_http3=False,
        enable_access_logs=False,
        backend=SCALEWAY_LB_BACKENDS[0],
        lb=_LB_SUMMARY,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]
