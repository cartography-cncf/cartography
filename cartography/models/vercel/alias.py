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
class VercelAliasNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    alias: PropertyRef = PropertyRef("alias", extra_index=True)
    deployment_id: PropertyRef = PropertyRef("deploymentId")
    project_id: PropertyRef = PropertyRef("projectId")
    created_at: PropertyRef = PropertyRef("createdAt")


@dataclass(frozen=True)
class VercelAliasToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelAlias)
class VercelAliasToTeamRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelAliasToTeamRelProperties = VercelAliasToTeamRelProperties()


@dataclass(frozen=True)
class VercelAliasToDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelAlias)-[:DEPLOYED_TO]->(:VercelDeployment)
class VercelAliasToDeploymentRel(CartographyRelSchema):
    target_node_label: str = "VercelDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("deploymentId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED_TO"
    properties: VercelAliasToDeploymentRelProperties = (
        VercelAliasToDeploymentRelProperties()
    )


@dataclass(frozen=True)
class VercelAliasToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelAlias)-[:BELONGS_TO_PROJECT]->(:VercelProject)
class VercelAliasToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO_PROJECT"
    properties: VercelAliasToProjectRelProperties = VercelAliasToProjectRelProperties()


@dataclass(frozen=True)
class VercelAliasSchema(CartographyNodeSchema):
    label: str = "VercelAlias"
    properties: VercelAliasNodeProperties = VercelAliasNodeProperties()
    sub_resource_relationship: VercelAliasToTeamRel = VercelAliasToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelAliasToDeploymentRel(), VercelAliasToProjectRel()],
    )
