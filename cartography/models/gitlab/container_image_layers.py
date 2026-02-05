"""
GitLab Container Image Layer Schema

Represents individual layers within container images stored in GitLab container registries.
Layers are identified by their digest (sha256:...) and can be shared across multiple images
through Docker's layer deduplication mechanism.

Each layer represents a filesystem diff applied during container image construction.
Layers are ordered from base (position 0) to top (highest position).

See: https://distribution.github.io/distribution/spec/manifest-v2-2/
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitLabContainerImageLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    diff_id: PropertyRef = PropertyRef("diff_id")
    media_type: PropertyRef = PropertyRef("media_type")
    size: PropertyRef = PropertyRef("size")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerImageLayerToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerImageLayerToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabContainerImageLayer to GitLabOrganization.
    Layers are scoped to organizations for cleanup and to allow cross-image deduplication.
    """

    target_node_label: str = "GitLabOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabContainerImageLayerToOrgRelProperties = (
        GitLabContainerImageLayerToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerImageLayerSchema(CartographyNodeSchema):
    """
    Schema for GitLab Container Image Layer nodes.

    Relationships:
    - RESOURCE: Sub-resource to GitLabOrganization for cleanup
    - HAS_LAYER: Inward relationship from GitLabContainerImage (defined in image schema)
    """

    label: str = "GitLabContainerImageLayer"
    properties: GitLabContainerImageLayerNodeProperties = (
        GitLabContainerImageLayerNodeProperties()
    )
    sub_resource_relationship: GitLabContainerImageLayerToOrgRel = (
        GitLabContainerImageLayerToOrgRel()
    )
