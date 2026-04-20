from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class VercelSecureComputeNetworkNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    region: PropertyRef = PropertyRef("region")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("createdAt")


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
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    environments: PropertyRef = PropertyRef("environments")
    passive_environments: PropertyRef = PropertyRef("passive_environments")


@dataclass(frozen=True)
# (:VercelSecureComputeNetwork)-[:CONNECTS {environments, passive_environments}]->(:VercelProject)
class VercelNetworkToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId")},
    )
    source_node_label: str = "VercelSecureComputeNetwork"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("networkId")},
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
