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
class GCPPolicyBindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    role: PropertyRef = PropertyRef("role")
    resource: PropertyRef = PropertyRef("resource")
    resource_type: PropertyRef = PropertyRef("resource_type")
    members: PropertyRef = PropertyRef("members")
    has_condition: PropertyRef = PropertyRef("has_condition")
    condition_title: PropertyRef = PropertyRef("condition_title")
    condition_expression: PropertyRef = PropertyRef("condition_expression")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPPolicyBindingToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPPolicyBindingToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPPolicyBindingToProjectRelProperties = (
        GCPPolicyBindingToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingToPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPPolicyBindingToPrincipalRel(CartographyRelSchema):
    target_node_label: str = "GCPPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ALLOW_POLICY"
    properties: GCPPolicyBindingToPrincipalRelProperties = (
        GCPPolicyBindingToPrincipalRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPPolicyBindingToRoleRel(CartographyRelSchema):
    target_node_label: str = "GCPRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("role")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ROLE"
    properties: GCPPolicyBindingToRoleRelProperties = (
        GCPPolicyBindingToRoleRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingSchema(CartographyNodeSchema):
    label: str = "GCPPolicyBinding"
    properties: GCPPolicyBindingNodeProperties = GCPPolicyBindingNodeProperties()
    sub_resource_relationship: GCPPolicyBindingToProjectRel = (
        GCPPolicyBindingToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPPolicyBindingToPrincipalRel(),
            GCPPolicyBindingToRoleRel(),
        ]
    )
