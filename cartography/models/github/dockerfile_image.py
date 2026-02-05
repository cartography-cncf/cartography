"""
Data model for linking GitHub repositories to container images via Dockerfile matching.

This uses MatchLinks to connect existing GitHubRepository nodes to ImageTag
nodes based on Dockerfile command matching analysis. By matching on repo_uri, we link
to ALL images in a container registry repository with a single relationship definition.

Works with any container registry that follows the cartography image ontology
(ECR, GCR, etc.) by using the generic ImageTag label.
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
class GitHubRepoBuiltFromMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the BUILT_FROM relationship between ImageTag and GitHubRepository.
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
class GitHubRepoBuiltFromMatchLink(CartographyRelSchema):
    """
    MatchLink schema for connecting ImageTag nodes to GitHubRepository nodes
    based on Dockerfile command matching.

    Direction: (ImageTag)-[:BUILT_FROM]->(GitHubRepository)

    Uses the generic ImageTag label from the cartography image ontology, which works
    across different container registries (ECR, GCR, etc.).

    By matching on repo_uri, this creates relationships to ALL images in a
    registry repository that were built from the Dockerfile in the GitHub repository.
    The confidence score is based on command similarity analysis.
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("repo_url"),
        }
    )
    # Use generic ImageTag label instead of ECRRepositoryImage for cross-registry support
    source_node_label: str = "ImageTag"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "repo_uri": PropertyRef("registry_repo_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILT_FROM"
    properties: GitHubRepoBuiltFromMatchLinkProperties = (
        GitHubRepoBuiltFromMatchLinkProperties()
    )


@dataclass(frozen=True)
class ImageBuiltByWorkflowMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the BUILT_BY relationship between Image and GitHubWorkflow.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Workflow run information from SLSA provenance
    run_number: PropertyRef = PropertyRef("run_number")


@dataclass(frozen=True)
class ImageBuiltByWorkflowMatchLink(CartographyRelSchema):
    """
    MatchLink schema for connecting Image nodes to GitHubWorkflow nodes
    based on SLSA provenance attestations.

    Direction: (Image)-[:BUILT_BY]->(GitHubWorkflow)

    This relationship is created when SLSA provenance attestations specify
    the GitHub Actions workflow that built the container image. The matching
    uses repo_url + path to identify the correct workflow. The run_number
    property indicates which specific workflow run produced the image.
    """

    target_node_label: str = "GitHubWorkflow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "repo_url": PropertyRef("workflow_repo_url"),
            "path": PropertyRef("workflow_path"),
        }
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "digest": PropertyRef("image_digest"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILT_BY"
    properties: ImageBuiltByWorkflowMatchLinkProperties = (
        ImageBuiltByWorkflowMatchLinkProperties()
    )
