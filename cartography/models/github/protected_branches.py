"""
Data model for GitHub Protected Branches.

Schema for GitHubProtectedBranch nodes and their relationships to GitHubRepository.
Based on GitHub GraphQL API: https://docs.github.com/en/graphql/reference/objects#branchprotectionrule
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubProtectedBranchNodeProperties(CartographyNodeProperties):
    """
    Properties of a GitHubProtectedBranch node.
    Maps to GitHub's BranchProtectionRule GraphQL type.
    """

    id: PropertyRef = PropertyRef("id")
    pattern: PropertyRef = PropertyRef("pattern")
    allows_deletions: PropertyRef = PropertyRef("allows_deletions")
    allows_force_pushes: PropertyRef = PropertyRef("allows_force_pushes")
    dismisses_stale_reviews: PropertyRef = PropertyRef("dismisses_stale_reviews")
    is_admin_enforced: PropertyRef = PropertyRef("is_admin_enforced")
    requires_approving_reviews: PropertyRef = PropertyRef("requires_approving_reviews")
    required_approving_review_count: PropertyRef = PropertyRef(
        "required_approving_review_count"
    )
    requires_code_owner_reviews: PropertyRef = PropertyRef(
        "requires_code_owner_reviews"
    )
    requires_commit_signatures: PropertyRef = PropertyRef("requires_commit_signatures")
    requires_linear_history: PropertyRef = PropertyRef("requires_linear_history")
    requires_status_checks: PropertyRef = PropertyRef("requires_status_checks")
    requires_strict_status_checks: PropertyRef = PropertyRef(
        "requires_strict_status_checks"
    )
    restricts_pushes: PropertyRef = PropertyRef("restricts_pushes")
    restricts_review_dismissals: PropertyRef = PropertyRef(
        "restricts_review_dismissals"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubProtectedBranchToRepositoryRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between a protected branch rule and its repository.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubProtectedBranchToRepositoryRel(CartographyRelSchema):
    """
    Relationship: (GitHubRepository)-[:PROTECTS]->(GitHubProtectedBranch)
    A repository can have multiple protection rules (for different branch patterns).
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PROTECTS"
    properties: GitHubProtectedBranchToRepositoryRelProperties = (
        GitHubProtectedBranchToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GitHubProtectedBranchSchema(CartographyNodeSchema):
    """
    Schema for GitHubProtectedBranch nodes.

    Example Cypher query to use this data:
    ```
    MATCH (repo:GitHubRepository)-[:PROTECTS]->(pb:GitHubProtectedBranch)
    WHERE pb.pattern = 'main'
      AND (pb.requires_approving_reviews = false OR pb.required_approving_review_count = 0)
    RETURN repo.name as UnprotectedRepo
    ```
    """

    label: str = "GitHubProtectedBranch"
    properties: GitHubProtectedBranchNodeProperties = (
        GitHubProtectedBranchNodeProperties()
    )
    sub_resource_relationship: GitHubProtectedBranchToRepositoryRel = (
        GitHubProtectedBranchToRepositoryRel()
    )
