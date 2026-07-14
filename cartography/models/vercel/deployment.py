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
class VercelDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="Deployment ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    name: PropertyRef = PropertyRef("name", description="Deployment name.")
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="Public deployment URL."
    )
    created_at: PropertyRef = PropertyRef(
        "created", description="Timestamp when the deployment was created."
    )
    ready_at: PropertyRef = PropertyRef(
        "ready", description="Timestamp when the deployment became ready."
    )
    state: PropertyRef = PropertyRef("state", description="Deployment state.")
    target: PropertyRef = PropertyRef(
        "target", description="Target environment for the deployment."
    )
    source: PropertyRef = PropertyRef(
        "source", description="Source that initiated the deployment."
    )
    creator_uid: PropertyRef = PropertyRef(
        "creator_uid", description="ID of the user who created the deployment."
    )
    meta_git_commit_sha: PropertyRef = PropertyRef(
        "meta_git_commit_sha", description="Git commit SHA deployed."
    )
    meta_git_branch: PropertyRef = PropertyRef(
        "meta_git_branch", description="Git branch deployed."
    )


@dataclass(frozen=True)
class VercelDeploymentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelDeployment)
class VercelDeploymentToProjectRel(CartographyRelSchema):
    """The Vercel project contains this deployment as a resource."""

    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelDeploymentToProjectRelProperties = (
        VercelDeploymentToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelDeploymentToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelDeployment)-[:CREATED_BY]->(:VercelUser)
class VercelDeploymentToUserRel(CartographyRelSchema):
    """The Vercel deployment was created by this user."""

    target_node_label: str = "VercelUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("creator_uid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: VercelDeploymentToUserRelProperties = (
        VercelDeploymentToUserRelProperties()
    )


@dataclass(frozen=True)
class VercelDeploymentSchema(CartographyNodeSchema):
    """An individual Vercel deployment of a project."""

    label: str = "VercelDeployment"
    properties: VercelDeploymentNodeProperties = VercelDeploymentNodeProperties()
    sub_resource_relationship: VercelDeploymentToProjectRel = (
        VercelDeploymentToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelDeploymentToUserRel()],
    )
