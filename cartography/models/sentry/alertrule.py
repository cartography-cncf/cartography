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
class SentryAlertRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    date_created: PropertyRef = PropertyRef("date_created")
    action_match: PropertyRef = PropertyRef("actionMatch")
    filter_match: PropertyRef = PropertyRef("filterMatch")
    frequency: PropertyRef = PropertyRef("frequency")
    environment: PropertyRef = PropertyRef("environment")
    status: PropertyRef = PropertyRef("status")
    project_slug: PropertyRef = PropertyRef("project_slug")


@dataclass(frozen=True)
class SentryOrganizationToAlertRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryOrganization)-[:RESOURCE]->(:SentryAlertRule)
# Sub-resource scoped to org so cleanup catches rules from deleted projects
@dataclass(frozen=True)
class SentryOrganizationToAlertRuleRel(CartographyRelSchema):
    target_node_label: str = "SentryOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentryOrganizationToAlertRuleRelProperties = (
        SentryOrganizationToAlertRuleRelProperties()
    )


@dataclass(frozen=True)
class SentryProjectToAlertRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryProject)-[:HAS_RULE]->(:SentryAlertRule)
@dataclass(frozen=True)
class SentryProjectToAlertRuleRel(CartographyRelSchema):
    target_node_label: str = "SentryProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULE"
    properties: SentryProjectToAlertRuleRelProperties = (
        SentryProjectToAlertRuleRelProperties()
    )


@dataclass(frozen=True)
class SentryAlertRuleSchema(CartographyNodeSchema):
    label: str = "SentryAlertRule"
    properties: SentryAlertRuleNodeProperties = SentryAlertRuleNodeProperties()
    sub_resource_relationship: SentryOrganizationToAlertRuleRel = (
        SentryOrganizationToAlertRuleRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[SentryProjectToAlertRuleRel()],
    )
