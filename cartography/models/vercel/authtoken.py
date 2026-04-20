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
class VercelAuthTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    origin: PropertyRef = PropertyRef("origin")
    active_at: PropertyRef = PropertyRef("activeAt")
    created_at: PropertyRef = PropertyRef("createdAt")
    expires_at: PropertyRef = PropertyRef("expiresAt")


@dataclass(frozen=True)
class VercelAuthTokenToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelAuthToken)
class VercelAuthTokenToTeamRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelAuthTokenToTeamRelProperties = (
        VercelAuthTokenToTeamRelProperties()
    )


@dataclass(frozen=True)
class VercelAuthTokenToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelAuthToken)-[:OWNED_BY]->(:VercelUser)
class VercelAuthTokenToUserRel(CartographyRelSchema):
    target_node_label: str = "VercelUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: VercelAuthTokenToUserRelProperties = (
        VercelAuthTokenToUserRelProperties()
    )


@dataclass(frozen=True)
class VercelAuthTokenSchema(CartographyNodeSchema):
    label: str = "VercelAuthToken"
    properties: VercelAuthTokenNodeProperties = VercelAuthTokenNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    sub_resource_relationship: VercelAuthTokenToTeamRel = VercelAuthTokenToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelAuthTokenToUserRel()],
    )
