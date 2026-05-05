from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPPolicyBindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    role: PropertyRef = PropertyRef("role")
    resource: PropertyRef = PropertyRef("resource")
    resource_type: PropertyRef = PropertyRef("resource_type")
    members: PropertyRef = PropertyRef("members")
    is_public: PropertyRef = PropertyRef("is_public")
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


@dataclass(frozen=True)
class GCPPolicyBindingAppliesToRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPPolicyBindingAppliesToMatchLink(CartographyRelSchema):
    """
    MatchLink schema that connects a GCPPolicyBinding to the concrete resource
    node it applies to.

    target_node_label is set dynamically at instantiation (e.g. "GCPProject",
    "GCPBucket") so a single binding can be matched unambiguously by (id, label)
    — raw resource_id alone is ambiguous across resource types.
    """

    source_node_label: str = "GCPPolicyBinding"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("binding_id")},
    )
    target_node_label: str = "GCPResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: GCPPolicyBindingAppliesToRelProperties = (
        GCPPolicyBindingAppliesToRelProperties()
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="GCPProject",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
