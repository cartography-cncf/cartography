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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class RailwayApiTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    # Railway's own redacted prefix, not the secret itself.
    display_token: PropertyRef = PropertyRef("displayToken")
    workspace_id: PropertyRef = PropertyRef("workspaceId")
    expires_at: PropertyRef = PropertyRef("expiresAt", extra_index=True)


@dataclass(frozen=True)
class RailwayApiTokenToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayWorkspace)-[:RESOURCE]->(:RailwayApiToken)
class RailwayApiTokenToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "RailwayWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayApiTokenToWorkspaceRelProperties = (
        RailwayApiTokenToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class RailwayApiTokenToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayApiToken)-[:OWNED_BY]->(:RailwayUser)
# Required by ONTOLOGY_REL_CONSTRAINTS: APIKey -> UserAccount must be OWNED_BY.
class RailwayApiTokenToUserRel(CartographyRelSchema):
    target_node_label: str = "RailwayUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: RailwayApiTokenToUserRelProperties = (
        RailwayApiTokenToUserRelProperties()
    )


@dataclass(frozen=True)
class RailwayApiTokenSchema(CartographyNodeSchema):
    label: str = "RailwayApiToken"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    properties: RailwayApiTokenNodeProperties = RailwayApiTokenNodeProperties()
    sub_resource_relationship: RailwayApiTokenToWorkspaceRel = (
        RailwayApiTokenToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayApiTokenToUserRel(),
        ],
    )
