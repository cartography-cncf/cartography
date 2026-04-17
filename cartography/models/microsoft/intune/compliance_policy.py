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
    id: PropertyRef = PropertyRef("id")
    display_name: PropertyRef = PropertyRef("display_name")
    description: PropertyRef = PropertyRef("description")
    platform: PropertyRef = PropertyRef("platform")
    version: PropertyRef = PropertyRef("version")
    created_date_time: PropertyRef = PropertyRef("created_date_time")
    last_modified_date_time: PropertyRef = PropertyRef("last_modified_date_time")
    applies_to_all_users: PropertyRef = PropertyRef("applies_to_all_users")
    applies_to_all_devices: PropertyRef = PropertyRef("applies_to_all_devices")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IntuneCompliancePolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:IntuneCompliancePolicy)<-[:RESOURCE]-(:EntraTenant)
@dataclass(frozen=True)
class IntuneCompliancePolicyToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
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
