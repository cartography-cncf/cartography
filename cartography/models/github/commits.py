"""
Data model for GitHub commit tracking, specifically for tracking which GitHubUsers have committed
to which GitHubRepositories in the last 30 days.

This uses MatchLinks to connect existing GitHubUser nodes to GitHubRepository nodes based on
commit data from a separate GitHub API call.
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
class GitHubUserCommittedToRepoRelProperties(CartographyRelProperties):
    """
    Properties for the COMMITTED_TO relationship between GitHubUser and GitHubRepository.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Rich relationship properties
    commit_count: PropertyRef = PropertyRef("commit_count")
    last_commit_date: PropertyRef = PropertyRef("last_commit_date")
    first_commit_date: PropertyRef = PropertyRef("first_commit_date")


@dataclass(frozen=True)
class GitHubUserCommittedToRepoRel(CartographyRelSchema):
    """
    MatchLink schema for connecting GitHubUser nodes to GitHubRepository nodes
    based on commits in the last 30 days.
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("repo_url"),
        }
    )
    source_node_label: str = "GitHubUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("user_url"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "COMMITTED_TO"
    properties: GitHubUserCommittedToRepoRelProperties = (
        GitHubUserCommittedToRepoRelProperties()
    )
