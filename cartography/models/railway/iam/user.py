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
class RailwayUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    two_factor_auth_enabled: PropertyRef = PropertyRef("twoFactorAuthEnabled")


@dataclass(frozen=True)
class RailwayUserToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayWorkspace)-[:RESOURCE]->(:RailwayUser)
class RailwayUserToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "RailwayWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayUserToWorkspaceRelProperties = (
        RailwayUserToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class RailwayUserMemberOfWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
# (:RailwayUser)-[:MEMBER_OF]->(:RailwayWorkspace)
# The workspace role rides on this edge rather than on the node: a user holds one role per
# workspace and a different one per project. Only one workspace is in scope per sync, so a
# plain rel is unambiguous here; project membership needs a MatchLink (see project_membership).
class RailwayUserMemberOfWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "RailwayWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: RailwayUserMemberOfWorkspaceRelProperties = (
        RailwayUserMemberOfWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class RailwayUserSchema(CartographyNodeSchema):
    label: str = "RailwayUser"
    # RailwayPrincipal: cross-provider IAM principal umbrella, mirroring AWSPrincipal /
    # ScalewayPrincipal. UserAccount drives the ontology mapping.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount", "RailwayPrincipal"],
    )
    properties: RailwayUserNodeProperties = RailwayUserNodeProperties()
    sub_resource_relationship: RailwayUserToWorkspaceRel = RailwayUserToWorkspaceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayUserMemberOfWorkspaceRel(),
        ],
    )
