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
class GitLabProjectPackagedFromMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the PACKAGED_FROM relationship between Image and GitLabProject.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    match_method: PropertyRef = PropertyRef(
        "match_method",
        description=(
            "Matching method: provenance, dockerfile_analysis, or "
            "dockerfile_singleton_fallback."
        ),
    )

    # Dockerfile matching properties (only populated for dockerfile_analysis method)
    dockerfile_path: PropertyRef = PropertyRef(
        "dockerfile_path",
        description="Path of the Dockerfile associated with the image.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence score for the image-to-project match.",
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
class GitLabProjectProvenancePackagedFromMatchLink(CartographyRelSchema):
    """Links an image to the GitLab project that packaged it."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "web_url": PropertyRef("project_url"),
        }
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "source_uri": PropertyRef("project_url"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_FROM"
    properties: GitLabProjectPackagedFromMatchLinkProperties = (
        GitLabProjectPackagedFromMatchLinkProperties()
    )


@dataclass(frozen=True)
class GitLabProjectDockerfilePackagedFromMatchLink(CartographyRelSchema):
    """Links an image to the GitLab project that packaged it."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "web_url": PropertyRef("project_url"),
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
    properties: GitLabProjectPackagedFromMatchLinkProperties = (
        GitLabProjectPackagedFromMatchLinkProperties()
    )
