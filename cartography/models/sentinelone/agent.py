from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class S1AgentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="SentinelOne agent ID.",
    )
    uuid: PropertyRef = PropertyRef(
        "uuid",
        extra_index=True,
        description="SentinelOne agent UUID.",
    )
    computer_name: PropertyRef = PropertyRef(
        "computer_name",
        extra_index=True,
        description="Endpoint computer name.",
    )
    public_ip: PropertyRef = PropertyRef(
        "public_ip",
        extra_index=True,
        description="Public IP address reported for the endpoint.",
    )
    local_ips: PropertyRef = PropertyRef(
        "local_ips",
        description="Local IP addresses reported for the endpoint.",
    )
    firewall_enabled: PropertyRef = PropertyRef(
        "firewall_enabled",
        description="Whether the endpoint firewall is enabled.",
    )
    os_name: PropertyRef = PropertyRef(
        "os_name",
        description="Endpoint operating system name.",
    )
    os_revision: PropertyRef = PropertyRef(
        "os_revision",
        description="Endpoint operating system revision.",
    )
    domain: PropertyRef = PropertyRef(
        "domain",
        description="Domain joined by the endpoint.",
    )
    last_active: PropertyRef = PropertyRef(
        "last_active",
        description="Timestamp of the agent's last activity.",
    )
    last_successful_scan: PropertyRef = PropertyRef(
        "last_successful_scan",
        description="Timestamp of the agent's last successful scan.",
    )
    scan_status: PropertyRef = PropertyRef(
        "scan_status",
        description="Status of the agent's latest scan.",
    )
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        extra_index=True,
        description="Endpoint serial number.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class S1AgentToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S1AgentToAccountRel(CartographyRelSchema):
    """Links a SentinelOne account to one of its agents."""

    target_node_label: str = "S1Account"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("S1_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S1AgentToAccountRelProperties = S1AgentToAccountRelProperties()


@dataclass(frozen=True)
class S1AgentSchema(CartographyNodeSchema):
    """A SentinelOne agent installed on an endpoint device."""

    label: str = "S1Agent"
    properties: S1AgentNodeProperties = S1AgentNodeProperties()
    sub_resource_relationship: S1AgentToAccountRel = S1AgentToAccountRel()
