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

    # Match method: "provenance" (from SLSA attestation) or "dockerfile_analysis" (from command matching)
    match_method: PropertyRef = PropertyRef("match_method")

    # Dockerfile matching properties (only populated for dockerfile_analysis method)
    dockerfile_path: PropertyRef = PropertyRef("dockerfile_path")
    confidence: PropertyRef = PropertyRef("confidence")
    matched_commands: PropertyRef = PropertyRef("matched_commands")
    total_commands: PropertyRef = PropertyRef("total_commands")
    command_similarity: PropertyRef = PropertyRef("command_similarity")


@dataclass(frozen=True)
class GitLabProjectProvenancePackagedFromMatchLink(CartographyRelSchema):
    """
    MatchLink for SLSA provenance: (Image)-[:PACKAGED_FROM]->(GitLabProject).

    Matches Image.source_uri to GitLabProject.id using the same project URL value.
    No pre-query needed: just pass the project URLs from the projects list.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_url"),
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
    """
    MatchLink for Dockerfile analysis: (Image)-[:PACKAGED_FROM]->(GitLabProject).

    Matches Image.digest to the specific image analyzed by the matching algorithm.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_url"),
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
