from dataclasses import dataclass
from typing import Optional

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
class ScalewayRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    permission_sets_scope_type: PropertyRef = PropertyRef("permission_sets_scope_type")
    condition: PropertyRef = PropertyRef("condition")
    permission_set_names: PropertyRef = PropertyRef("permission_set_names")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayRuleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayRule)
class ScalewayRuleToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayRuleToOrganizationRelProperties = (
        ScalewayRuleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayRuleToPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayPolicy)-[:HAS]->(:ScalewayRule)
class ScalewayRuleToPolicyRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayRuleToPolicyRelProperties = ScalewayRuleToPolicyRelProperties()


@dataclass(frozen=True)
class ScalewayRuleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayRule)-[:SCOPED_TO]->(:ScalewayProject)
class ScalewayRuleToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCOPED_TO"
    properties: ScalewayRuleToProjectRelProperties = (
        ScalewayRuleToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayRuleSchema(CartographyNodeSchema):
    label: str = "ScalewayRule"
    properties: ScalewayRuleNodeProperties = ScalewayRuleNodeProperties()
    sub_resource_relationship: ScalewayRuleToOrganizationRel = (
        ScalewayRuleToOrganizationRel()
    )
    other_relationships: Optional[OtherRelationships] = OtherRelationships(
        [
            ScalewayRuleToPolicyRel(),
            ScalewayRuleToProjectRel(),
        ]
    )
