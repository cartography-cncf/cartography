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
    id: PropertyRef = PropertyRef("uid", description="Alias ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    alias: PropertyRef = PropertyRef(
        "alias", extra_index=True, description="Alias hostname."
    )
    deployment_id: PropertyRef = PropertyRef(
        "deploymentId", description="ID of the deployment targeted by the alias."
    )
    project_id: PropertyRef = PropertyRef(
        "projectId", description="ID of the project that owns the alias."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the alias was created."
    )


@dataclass(frozen=True)
class VercelAliasToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelAlias)
class VercelAliasToTeamRel(CartographyRelSchema):
    """The Vercel team contains this alias as a resource."""

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
    """The Vercel alias points to this deployment."""

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
    """The Vercel alias belongs to this project."""

    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO_PROJECT"
    properties: VercelAliasToProjectRelProperties = VercelAliasToProjectRelProperties()


@dataclass(frozen=True)
class VercelAliasSchema(CartographyNodeSchema):
    """A Vercel hostname alias that points to a deployment."""

    label: str = "VercelAlias"
    properties: VercelAliasNodeProperties = VercelAliasNodeProperties()
    sub_resource_relationship: VercelAliasToTeamRel = VercelAliasToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelAliasToDeploymentRel(), VercelAliasToProjectRel()],
    )
