from datetime import datetime

from dateutil.tz import tzutc
from scaleway.instance.v1 import SecurityGroup
from scaleway.instance.v1 import SecurityGroupRule
from scaleway.instance.v1 import ServerSummary

SCALEWAY_SECURITY_GROUPS = [
    SecurityGroup(
        id="b2c3d4e5-1111-4820-b8d6-0eef10cfcd6d",
        name="demo-sg",
        description="Demo security group",
        enable_default_security=True,
        inbound_default_policy="drop",
        outbound_default_policy="accept",
        organization="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        tags=["demo"],
        project_default=False,
        organization_default=False,
        stateful=True,
        state="available",
        zone="fr-par-1",
        creation_date=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        modification_date=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        servers=[
            ServerSummary(
                id="345627e9-18ff-47e0-b73d-3f38fddb4390", name="demo-server"
            ),
        ],
    )
]

SCALEWAY_SECURITY_GROUP_RULES = [
    SecurityGroupRule(
        id="aaaa1111-2222-4820-b8d6-0eef10cfcd6d",
        protocol="tcp",
        direction="inbound",
        action="accept",
        ip_range="0.0.0.0/0",
        position=1,
        editable=True,
        zone="fr-par-1",
        dest_port_from=22,
        dest_port_to=22,
    ),
    SecurityGroupRule(
        id="bbbb2222-3333-4820-b8d6-0eef10cfcd6d",
        protocol="any",
        direction="outbound",
        action="accept",
        ip_range="0.0.0.0/0",
        position=1,
        editable=True,
        zone="fr-par-1",
        dest_port_from=None,
        dest_port_to=None,
    ),
]
