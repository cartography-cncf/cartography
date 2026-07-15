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
class GitHubRepoPackagedFromMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the PACKAGED_FROM relationship between Image and GitHubRepository.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Match method: "provenance" (from SLSA attestation) or "dockerfile_analysis" (from command matching)
    match_method: PropertyRef = PropertyRef(
        "match_method",
        description="Method used to link the image to the repository.",
    )

    # Dockerfile matching properties (only populated for dockerfile_analysis method)
    dockerfile_path: PropertyRef = PropertyRef(
        "dockerfile_path",
        description="Path of the Dockerfile associated with the image.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence score for the image-to-repository match.",
    )
    matched_commands: PropertyRef = PropertyRef(
        "matched_commands",
        description="Number of image build commands matched to Dockerfile commands.",
    )
    total_commands: PropertyRef = PropertyRef(
        "total_commands",
        description="Command count used to normalize the Dockerfile comparison.",
    )
    command_similarity: PropertyRef = PropertyRef(
        "command_similarity",
        description="Similarity score between image build commands and Dockerfile commands.",
    )


@dataclass(frozen=True)
class GitHubRepoProvenancePackagedFromMatchLink(CartographyRelSchema):
    """Links an image to the GitHub repository that produced it."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("repo_url"),
        }
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "source_uri": PropertyRef("repo_url"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_FROM"
    properties: GitHubRepoPackagedFromMatchLinkProperties = (
        GitHubRepoPackagedFromMatchLinkProperties()
    )


@dataclass(frozen=True)
class GitHubRepoDockerfilePackagedFromMatchLink(CartographyRelSchema):
    """Links an image to the GitHub repository that produced it."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("repo_url"),
        }
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "digest": PropertyRef("image_digest"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_FROM"
    properties: GitHubRepoPackagedFromMatchLinkProperties = (
        GitHubRepoPackagedFromMatchLinkProperties()
    )


@dataclass(frozen=True)
class GitHubRepoPackageOwnerPackagedFromMatchLink(CartographyRelSchema):
    """Links an image to the GitHub repository that produced it."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("repo_url"),
        },
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "digest": PropertyRef("image_digest"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_FROM"
    properties: GitHubRepoPackagedFromMatchLinkProperties = (
        GitHubRepoPackagedFromMatchLinkProperties()
    )


@dataclass(frozen=True)
class ImagePackagedByWorkflowMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the PACKAGED_BY relationship between Image and GitHubWorkflow.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class ImagePackagedByWorkflowMatchLink(CartographyRelSchema):
    """Links an image to the GitHub workflow that packaged it."""

    target_node_label: str = "GitHubWorkflow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "repo_url": PropertyRef("repo_url"),
            "path": PropertyRef("workflow_path"),
        }
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "invocation_uri": PropertyRef("repo_url"),
            "invocation_workflow": PropertyRef("workflow_path"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_BY"
    properties: ImagePackagedByWorkflowMatchLinkProperties = (
        ImagePackagedByWorkflowMatchLinkProperties()
    )
