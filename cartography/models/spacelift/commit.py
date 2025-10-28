"""
Spacelift Git Commit data model.

A GitCommit represents a Git commit that triggered a Spacelift run.
It contains metadata about the commit including the author, message, and timestamp.
"""

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
class GitCommitNodeProperties(CartographyNodeProperties):
    """
    Properties for a Git Commit node.
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
class GitCommitToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a Commit and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitCommitToAccountRel(CartographyRelSchema):
    """
    RESOURCE relationship from a Commit to its Account.
    (:GitCommit)<-[:RESOURCE]-(:SpaceliftAccount)
    """

    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitCommitToAccountRelProperties = GitCommitToAccountRelProperties()


@dataclass(frozen=True)
class GitCommitToAuthorRelProperties(CartographyRelProperties):
    """
    Properties for the CONFIRMED relationship between a Commit and the User who confirmed it.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitCommitToAuthorRel(CartographyRelSchema):
    """
    CONFIRMED relationship from a Commit to the User who authored/confirmed it.
    (:GitCommit)-[:CONFIRMED]->(:SpaceliftUser)

    This links commits to the human developers who wrote and confirmed the code,
    even when the deployment was triggered by an automated system (vcs/commit).
    """

    target_node_label: str = "SpaceliftUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("author_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONFIRMED"
    properties: GitCommitToAuthorRelProperties = GitCommitToAuthorRelProperties()


@dataclass(frozen=True)
class GitCommitSchema(CartographyNodeSchema):
    """
    Schema for a Git Commit node.
    """

    label: str = "GitCommit"
    properties: GitCommitNodeProperties = GitCommitNodeProperties()
    sub_resource_relationship: GitCommitToAccountRel = GitCommitToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitCommitToAuthorRel(),
        ],
    )
