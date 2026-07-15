from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class TailscaleTailnetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "org",
        set_in_kwargs=True,
        description="ID of the Tailnet (name of the organization).",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    devices_approval_on: PropertyRef = PropertyRef(
        "devicesApprovalOn",
        description="Whether device approval is enabled for the tailnet.",
    )
    devices_auto_updates_on: PropertyRef = PropertyRef(
        "devicesAutoUpdatesOn",
        description="Whether auto updates are enabled for devices that belong to this tailnet.",
    )
    devices_key_duration_days: PropertyRef = PropertyRef(
        "devicesKeyDurationDays",
        description="The key expiry duration for devices on this tailnet.",
    )
    users_approval_on: PropertyRef = PropertyRef(
        "usersApprovalOn",
        description="Whether user approval is enabled for this tailnet.",
    )
    users_role_allowed_to_join_external_tailnets: PropertyRef = PropertyRef(
        "usersRoleAllowedToJoinExternalTailnets",
        description="Which user roles are allowed to join external tailnets.",
    )
    network_flow_logging_on: PropertyRef = PropertyRef(
        "networkFlowLoggingOn",
        description="Whether network flow logs are enabled for the tailnet.",
    )
    regional_routing_on: PropertyRef = PropertyRef(
        "regionalRoutingOn",
        description="Whether regional routing is enabled for the tailnet.",
    )
    posture_identity_collection_on: PropertyRef = PropertyRef(
        "postureIdentityCollectionOn",
        description="Whether identity collection is enabled for device posture integrations for the tailnet.",
    )


@dataclass(frozen=True)
class TailscaleTailnetSchema(CartographyNodeSchema):
    """Settings for a tailnet (aka Tenant)."""

    label: str = "TailscaleTailnet"
    properties: TailscaleTailnetNodeProperties = TailscaleTailnetNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
