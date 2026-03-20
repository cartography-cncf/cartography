from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SentryUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    role: PropertyRef = PropertyRef("orgRole")
    date_created: PropertyRef = PropertyRef("date_created")
    pending: PropertyRef = PropertyRef("pending")
    expired: PropertyRef = PropertyRef("expired")
    has_2fa: PropertyRef = PropertyRef("has2fa")


@dataclass(frozen=True)
class SentryOrganizationToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryOrganization)-[:RESOURCE]->(:SentryUser)
@dataclass(frozen=True)
class SentryOrganizationToUserRel(CartographyRelSchema):
    target_node_label: str = "SentryOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentryOrganizationToUserRelProperties = (
        SentryOrganizationToUserRelProperties()
    )


@dataclass(frozen=True)
class SentryUserToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryUser)-[:MEMBER_OF]->(:SentryTeam)
@dataclass(frozen=True)
class SentryUserToTeamMemberOfRel(CartographyRelSchema):
    target_node_label: str = "SentryTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: SentryUserToTeamRelProperties = SentryUserToTeamRelProperties()


# (:SentryUser)-[:ADMIN_OF]->(:SentryTeam)
@dataclass(frozen=True)
class SentryUserToTeamAdminOfRel(CartographyRelSchema):
    target_node_label: str = "SentryTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("admin_team_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_OF"
    properties: SentryUserToTeamRelProperties = SentryUserToTeamRelProperties()


@dataclass(frozen=True)
class SentryUserSchema(CartographyNodeSchema):
    label: str = "SentryUser"
    properties: SentryUserNodeProperties = SentryUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    sub_resource_relationship: SentryOrganizationToUserRel = (
        SentryOrganizationToUserRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SentryUserToTeamMemberOfRel(),
            SentryUserToTeamAdminOfRel(),
        ],
    )
