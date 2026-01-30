"""
Data model for linking GitHub repositories to ECR images via Dockerfile matching.

This uses MatchLinks to connect existing GitHubRepository nodes to ECRRepositoryImage
nodes based on Dockerfile command matching analysis. By matching on repo_uri, we link
to ALL images in an ECR repository with a single relationship definition.
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
class GitHubRepoBuiltFromRelProperties(CartographyRelProperties):
    """
    Properties for the BUILT_FROM relationship between ECRRepositoryImage and GitHubRepository.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Dockerfile matching properties
    dockerfile_path: PropertyRef = PropertyRef("dockerfile_path")
    confidence: PropertyRef = PropertyRef("confidence")
    matched_commands: PropertyRef = PropertyRef("matched_commands")
    total_commands: PropertyRef = PropertyRef("total_commands")
    command_similarity: PropertyRef = PropertyRef("command_similarity")


@dataclass(frozen=True)
class GitHubRepoBuiltFromRel(CartographyRelSchema):
    """
    MatchLink schema for connecting ECRRepositoryImage nodes to GitHubRepository nodes
    based on Dockerfile command matching.

    Direction: (ECRRepositoryImage)-[:BUILT_FROM]->(GitHubRepository)

    By matching on repo_uri, this creates relationships to ALL images in an ECR
    repository that were built from the Dockerfile in the GitHub repository.
    The confidence score is based on command similarity analysis.
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("repo_url"),
        }
    )
    source_node_label: str = "ECRRepositoryImage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "repo_uri": PropertyRef("ecr_repo_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILT_FROM"
    properties: GitHubRepoBuiltFromRelProperties = GitHubRepoBuiltFromRelProperties()
