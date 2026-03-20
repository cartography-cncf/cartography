from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SentryTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    date_created: PropertyRef = PropertyRef("date_created")
    member_count: PropertyRef = PropertyRef("memberCount")


@dataclass(frozen=True)
class SentryOrganizationToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryOrganization)-[:RESOURCE]->(:SentryTeam)
@dataclass(frozen=True)
class SentryOrganizationToTeamRel(CartographyRelSchema):
    target_node_label: str = "SentryOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentryOrganizationToTeamRelProperties = (
        SentryOrganizationToTeamRelProperties()
    )


@dataclass(frozen=True)
class SentryTeamSchema(CartographyNodeSchema):
    label: str = "SentryTeam"
    properties: SentryTeamNodeProperties = SentryTeamNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    sub_resource_relationship: SentryOrganizationToTeamRel = (
        SentryOrganizationToTeamRel()
    )
