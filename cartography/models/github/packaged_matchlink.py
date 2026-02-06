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
    match_method: PropertyRef = PropertyRef("match_method")

    # Dockerfile matching properties (only populated for dockerfile_analysis method)
    dockerfile_path: PropertyRef = PropertyRef("dockerfile_path")
    confidence: PropertyRef = PropertyRef("confidence")
    matched_commands: PropertyRef = PropertyRef("matched_commands")
    total_commands: PropertyRef = PropertyRef("total_commands")
    command_similarity: PropertyRef = PropertyRef("command_similarity")


@dataclass(frozen=True)
class GitHubRepoProvenancePackagedFromMatchLink(CartographyRelSchema):
    """
    MatchLink for SLSA provenance: (Image)-[:PACKAGED_FROM]->(GitHubRepository).

    Matches Image.source_uri to GitHubRepository.id using the same repo URL value.
    No pre-query needed: just pass the repo URLs from the repos list.
    """

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
    """
    MatchLink for Dockerfile analysis: (Image)-[:PACKAGED_FROM]->(GitHubRepository).

    Matches Image.digest to the specific image analyzed by the matching algorithm.
    """

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

    # Workflow run information from SLSA provenance
    run_number: PropertyRef = PropertyRef("run_number")


@dataclass(frozen=True)
class ImagePackagedByWorkflowMatchLink(CartographyRelSchema):
    """
    MatchLink schema for connecting Image nodes to GitHubWorkflow nodes
    based on SLSA provenance attestations.

    Direction: (Image)-[:PACKAGED_BY]->(GitHubWorkflow)

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
    rel_label: str = "PACKAGED_BY"
    properties: ImagePackagedByWorkflowMatchLinkProperties = (
        ImagePackagedByWorkflowMatchLinkProperties()
    )
