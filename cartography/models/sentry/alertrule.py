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
    id: PropertyRef = PropertyRef("id", description="Sentry alert rule ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Alert rule name.")
    date_created: PropertyRef = PropertyRef(
        "date_created",
        description="ISO 8601 timestamp when the alert rule was created.",
    )
    action_match: PropertyRef = PropertyRef(
        "actionMatch",
        description="Action matching logic: all, any, or none.",
    )
    filter_match: PropertyRef = PropertyRef(
        "filterMatch",
        description="Filter matching logic: all, any, or none.",
    )
    frequency: PropertyRef = PropertyRef(
        "frequency",
        description="Throttle interval in seconds.",
    )
    environment: PropertyRef = PropertyRef(
        "environment",
        description="Environment to which the rule applies.",
    )
    status: PropertyRef = PropertyRef("status", description="Alert rule status.")
    project_slug: PropertyRef = PropertyRef(
        "project_slug",
        description="Slug of the project containing the rule.",
    )


@dataclass(frozen=True)
class SentryOrganizationToAlertRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryOrganization)-[:RESOURCE]->(:SentryAlertRule)
# Sub-resource scoped to org so cleanup catches rules from deleted projects
@dataclass(frozen=True)
class SentryOrganizationToAlertRuleRel(CartographyRelSchema):
    """The organization contains the alert rule for scoped cleanup."""

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
    """The project has the alert rule."""

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
    """An issue alert rule configured on a Sentry project."""

    label: str = "SentryAlertRule"
    properties: SentryAlertRuleNodeProperties = SentryAlertRuleNodeProperties()
    sub_resource_relationship: SentryOrganizationToAlertRuleRel = (
        SentryOrganizationToAlertRuleRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[SentryProjectToAlertRuleRel()],
    )
