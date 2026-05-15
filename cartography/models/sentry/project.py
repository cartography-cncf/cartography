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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    platform: PropertyRef = PropertyRef("platform")
    date_created: PropertyRef = PropertyRef("date_created")
    first_event: PropertyRef = PropertyRef("first_event")


@dataclass(frozen=True)
class SentryOrganizationToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryOrganization)-[:RESOURCE]->(:SentryProject)
@dataclass(frozen=True)
class SentryOrganizationToProjectRel(CartographyRelSchema):
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
    target_node_label: str = "SentryTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_TEAM"
    properties: SentryProjectToTeamRelProperties = SentryProjectToTeamRelProperties()


@dataclass(frozen=True)
class SentryProjectSchema(CartographyNodeSchema):
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
