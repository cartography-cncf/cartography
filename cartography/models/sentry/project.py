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
class SentryProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Sentry project ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Project name.")
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="URL-friendly project identifier.",
    )
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Primary project platform.",
    )
    date_created: PropertyRef = PropertyRef(
        "date_created",
        description="ISO 8601 timestamp when the project was created.",
    )
    first_event: PropertyRef = PropertyRef(
        "first_event",
        description="ISO 8601 timestamp when the first event was received.",
    )


@dataclass(frozen=True)
class SentryOrganizationToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryOrganization)-[:RESOURCE]->(:SentryProject)
@dataclass(frozen=True)
class SentryOrganizationToProjectRel(CartographyRelSchema):
    """The organization contains the project."""

    target_node_label: str = "SentryOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentryOrganizationToProjectRelProperties = (
        SentryOrganizationToProjectRelProperties()
    )


@dataclass(frozen=True)
class SentryProjectToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryProject)-[:HAS_TEAM]->(:SentryTeam)
@dataclass(frozen=True)
class SentryProjectToTeamRel(CartographyRelSchema):
    """The project is assigned to the team."""

    target_node_label: str = "SentryTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_TEAM"
    properties: SentryProjectToTeamRelProperties = SentryProjectToTeamRelProperties()


@dataclass(frozen=True)
class SentryProjectSchema(CartographyNodeSchema):
    """A project in a Sentry organization."""

    label: str = "SentryProject"
    properties: SentryProjectNodeProperties = SentryProjectNodeProperties()
    sub_resource_relationship: SentryOrganizationToProjectRel = (
        SentryOrganizationToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SentryProjectToTeamRel(),
        ],
    )
