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
class SpaceliftGitCommitNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Git Commit node.
    """

    id: PropertyRef = PropertyRef("sha")  # Use SHA as the unique identifier
    sha: PropertyRef = PropertyRef("sha", extra_index=True)
    message: PropertyRef = PropertyRef("message")
    timestamp: PropertyRef = PropertyRef("timestamp")
    url: PropertyRef = PropertyRef("url")
    author_login: PropertyRef = PropertyRef("author_login", extra_index=True)
    author_name: PropertyRef = PropertyRef("author_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftGitCommitToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a Spacelift Git Commit and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftGitCommitToAccountRel(CartographyRelSchema):
    """
    RESOURCE relationship from a Spacelift Git Commit to its Account.
    (:SpaceliftGitCommit)<-[:RESOURCE]-(:SpaceliftAccount)
    """

    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("spacelift_account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpaceliftGitCommitToAccountRelProperties = (
        SpaceliftGitCommitToAccountRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftGitCommitToAuthorRelProperties(CartographyRelProperties):
    """
    Properties for the CONFIRMED relationship between a Spacelift Git Commit and the User who confirmed it.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftGitCommitToAuthorRel(CartographyRelSchema):
    """
    CONFIRMED relationship from a Spacelift Git Commit to the User who authored/confirmed it.
    (:SpaceliftGitCommit)-[:CONFIRMED]->(:SpaceliftUser)

    This links commits to the human developers who wrote and confirmed the code,
    even when the deployment was triggered by an automated system (vcs/commit).
    """

    target_node_label: str = "SpaceliftUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("author_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONFIRMED"
    properties: SpaceliftGitCommitToAuthorRelProperties = (
        SpaceliftGitCommitToAuthorRelProperties()
    )


@dataclass(frozen=True)
class GitHubUserToSpaceliftGitCommitRelProperties(CartographyRelProperties):
    """
    Properties for the PUSHED relationship between a GitHub User and a Spacelift Git Commit.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubUserToSpaceliftGitCommitRel(CartographyRelSchema):
    """
    PUSHED relationship from a GitHub User to a Spacelift Git Commit.
    """

    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"username": PropertyRef("author_login")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PUSHED"
    properties: GitHubUserToSpaceliftGitCommitRelProperties = (
        GitHubUserToSpaceliftGitCommitRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftGitCommitToRunRelProperties(CartographyRelProperties):
    """
    Properties for the COMMITTED relationship between a Spacelift Git Commit and a Run.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftGitCommitToRunRel(CartographyRelSchema):
    """
    COMMITTED relationship from a Spacelift Git Commit to the Run that uses it.
    (:SpaceliftGitCommit)-[:COMMITTED]->(:SpaceliftRun)
    """

    target_node_label: str = "SpaceliftRun"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"commit_sha": PropertyRef("sha")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "COMMITTED"
    properties: SpaceliftGitCommitToRunRelProperties = (
        SpaceliftGitCommitToRunRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftGitCommitSchema(CartographyNodeSchema):
    """
    Schema for a Spacelift Git Commit node.
    """

    label: str = "SpaceliftGitCommit"
    properties: SpaceliftGitCommitNodeProperties = SpaceliftGitCommitNodeProperties()
    sub_resource_relationship: SpaceliftGitCommitToAccountRel = (
        SpaceliftGitCommitToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SpaceliftGitCommitToAuthorRel(),
            SpaceliftGitCommitToRunRel(),
            GitHubUserToSpaceliftGitCommitRel(),
        ],
    )
