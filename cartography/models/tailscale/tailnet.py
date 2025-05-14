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
class TailscaleTailnetNodeProperties(CartographyNodeProperties):
    devices_approval_on: PropertyRef = PropertyRef("devicesApprovalOn")
    devices_auto_updates_on: PropertyRef = PropertyRef("devicesAutoUpdatesOn")
    devices_key_duration_days: PropertyRef = PropertyRef("devicesKeyDurationDays")
    users_approval_on: PropertyRef = PropertyRef("usersApprovalOn")
    users_role_allowed_to_join_external_tailnets: PropertyRef = PropertyRef(
        "usersRoleAllowedToJoinExternalTailnets"
    )
    network_flow_logging_on: PropertyRef = PropertyRef("networkFlowLoggingOn")
    regional_routing_on: PropertyRef = PropertyRef("regionalRoutingOn")
    posture_identity_collection_on: PropertyRef = PropertyRef(
        "postureIdentityCollectionOn"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TailscaleTailnetSchema(CartographyNodeSchema):
    label: str = "TailscaleTailnet"
    properties: TailscaleTailnetNodeProperties = TailscaleTailnetNodeProperties()
