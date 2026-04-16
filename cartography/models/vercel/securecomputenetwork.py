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
class VercelSecureComputeNetworkNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    region: PropertyRef = PropertyRef("region")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("createdAt")
    project_ids: PropertyRef = PropertyRef("project_ids")


@dataclass(frozen=True)
class VercelNetworkToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelSecureComputeNetwork)
class VercelNetworkToTeamRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelNetworkToTeamRelProperties = VercelNetworkToTeamRelProperties()


@dataclass(frozen=True)
class VercelNetworkToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelSecureComputeNetwork)-[:CONNECTS]->(:VercelProject)
class VercelNetworkToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS"
    properties: VercelNetworkToProjectRelProperties = (
        VercelNetworkToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelSecureComputeNetworkSchema(CartographyNodeSchema):
    label: str = "VercelSecureComputeNetwork"
    properties: VercelSecureComputeNetworkNodeProperties = (
        VercelSecureComputeNetworkNodeProperties()
    )
    sub_resource_relationship: VercelNetworkToTeamRel = VercelNetworkToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelNetworkToProjectRel()],
    )
