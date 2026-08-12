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
class ScalewayAuditTrailAlertRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    status: PropertyRef = PropertyRef("status")
    region: PropertyRef = PropertyRef("region")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayAuditTrailAlertRuleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayAuditTrailAlertRule)
class ScalewayAuditTrailAlertRuleToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayAuditTrailAlertRuleToProjectRelProperties = (
        ScalewayAuditTrailAlertRuleToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayAuditTrailAlertRuleSchema(CartographyNodeSchema):
    label: str = "ScalewayAuditTrailAlertRule"
    properties: ScalewayAuditTrailAlertRuleProperties = (
        ScalewayAuditTrailAlertRuleProperties()
    )
    sub_resource_relationship: ScalewayAuditTrailAlertRuleToProjectRel = (
        ScalewayAuditTrailAlertRuleToProjectRel()
    )
