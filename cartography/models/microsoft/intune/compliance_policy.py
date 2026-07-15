from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class IntuneCompliancePolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Intune compliance policy ID.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the compliance policy."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Administrator-provided policy description."
    )
    platform: PropertyRef = PropertyRef(
        "platform", description="Device platform targeted by the policy."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Version of the compliance policy."
    )
    created_date_time: PropertyRef = PropertyRef(
        "created_date_time", description="Timestamp when the policy was created."
    )
    last_modified_date_time: PropertyRef = PropertyRef(
        "last_modified_date_time",
        description="Timestamp when the policy was last modified.",
    )
    applies_to_all_users: PropertyRef = PropertyRef(
        "applies_to_all_users",
        description="Whether the policy applies to all licensed users.",
    )
    applies_to_all_devices: PropertyRef = PropertyRef(
        "applies_to_all_devices",
        description="Whether the policy applies to all managed devices.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class IntuneCompliancePolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:IntuneCompliancePolicy)<-[:RESOURCE]-(:AzureTenant)
@dataclass(frozen=True)
class IntuneCompliancePolicyToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its Intune compliance policies."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: IntuneCompliancePolicyRelProperties = (
        IntuneCompliancePolicyRelProperties()
    )


# (:IntuneCompliancePolicy)-[:ASSIGNED_TO]->(:EntraGroup)
@dataclass(frozen=True)
class IntuneCompliancePolicyToEntraGroupRel(CartographyRelSchema):
    """Links an Intune compliance policy to an assigned Entra group."""

    target_node_label: str = "EntraGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: IntuneCompliancePolicyRelProperties = (
        IntuneCompliancePolicyRelProperties()
    )


@dataclass(frozen=True)
class IntuneCompliancePolicySchema(CartographyNodeSchema):
    """A device compliance policy configured in Microsoft Intune."""

    label: str = "IntuneCompliancePolicy"
    properties: IntuneCompliancePolicyNodeProperties = (
        IntuneCompliancePolicyNodeProperties()
    )
    sub_resource_relationship: IntuneCompliancePolicyToTenantRel = (
        IntuneCompliancePolicyToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            IntuneCompliancePolicyToEntraGroupRel(),
        ],
    )
