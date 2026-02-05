"""
Data model for linking GitLab projects to container images via Dockerfile matching.

This uses MatchLinks to connect existing GitLabProject nodes to ImageTag
nodes based on Dockerfile command matching analysis. By matching on repository_location,
we link to ALL images in a container repository with a single relationship definition.

Works with GitLab container registries by using the generic ImageTag label
(applied to GitLabContainerRepositoryTag nodes).
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitLabProjectBuiltFromMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the BUILT_FROM relationship between ImageTag and GitLabProject.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Match method: "provenance" (from SLSA attestation) or "dockerfile_analysis" (from command matching)
    match_method: PropertyRef = PropertyRef("match_method")

    # Dockerfile matching properties (only populated for dockerfile_analysis method)
    dockerfile_path: PropertyRef = PropertyRef("dockerfile_path")
    confidence: PropertyRef = PropertyRef("confidence")
    matched_commands: PropertyRef = PropertyRef("matched_commands")
    total_commands: PropertyRef = PropertyRef("total_commands")
    command_similarity: PropertyRef = PropertyRef("command_similarity")


@dataclass(frozen=True)
class GitLabProjectBuiltFromMatchLink(CartographyRelSchema):
    """
    MatchLink schema for connecting ImageTag nodes to GitLabProject nodes
    based on Dockerfile command matching.

    Direction: (ImageTag)-[:BUILT_FROM]->(GitLabProject)

    Uses the generic ImageTag label from the cartography image ontology, which maps
    to GitLabContainerRepositoryTag nodes.

    By matching on repository_location, this creates relationships to ALL images in a
    registry repository that were built from the Dockerfile in the GitLab project.
    The confidence score is based on command similarity analysis.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_url"),
        }
    )
    # Use generic ImageTag label for cross-registry support
    source_node_label: str = "ImageTag"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "repository_location": PropertyRef("registry_repo_location"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILT_FROM"
    properties: GitLabProjectBuiltFromMatchLinkProperties = (
        GitLabProjectBuiltFromMatchLinkProperties()
    )
