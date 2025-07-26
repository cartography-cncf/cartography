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
    id: PropertyRef = PropertyRef("id", extra_index=True)
    uuid: PropertyRef = PropertyRef("uuid", extra_index=True)
    computer_name: PropertyRef = PropertyRef("computer_name", extra_index=True)
    firewall_enabled: PropertyRef = PropertyRef("firewall_enabled")
    os_name: PropertyRef = PropertyRef("os_name")
    os_revision: PropertyRef = PropertyRef("os_revision")
    domain: PropertyRef = PropertyRef("domain")
    last_active: PropertyRef = PropertyRef("last_active")
    last_successful_scan: PropertyRef = PropertyRef("last_successful_scan")
    scan_status: PropertyRef = PropertyRef("scan_status")
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S1AgentToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1Agent)<-[:RESOURCE]-(:S1Account)
class S1AgentToAccount(CartographyRelSchema):
    target_node_label: str = "S1Account"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("S1_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S1AgentToAccountRelProperties = S1AgentToAccountRelProperties()


@dataclass(frozen=True)
class S1AgentSchema(CartographyNodeSchema):
    label: str = "S1Agent"
    properties: S1AgentNodeProperties = S1AgentNodeProperties()
    sub_resource_relationship: S1AgentToAccount = S1AgentToAccount()
