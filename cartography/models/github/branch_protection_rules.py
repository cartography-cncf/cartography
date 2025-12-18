"""
Data model for GitHub Branch Protection Rules.

Schema for GitHubBranchProtectionRule nodes and their relationships to GitHubRepository.
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
class GitHubBranchProtectionRuleNodeProperties(CartographyNodeProperties):
    """
    Properties of a GitHubBranchProtectionRule node.
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
class GitHubBranchProtectionRuleToRepositoryRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between a branch protection rule and its repository.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubBranchProtectionRuleToRepositoryRel(CartographyRelSchema):
    """
    Relationship: (GitHubRepository)-[:HAS_RULE]->(GitHubBranchProtectionRule)
    A repository can have multiple protection rules (for different branch patterns).
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULE"
    properties: GitHubBranchProtectionRuleToRepositoryRelProperties = (
        GitHubBranchProtectionRuleToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GitHubBranchProtectionRuleSchema(CartographyNodeSchema):
    label: str = "GitHubBranchProtectionRule"
    properties: GitHubBranchProtectionRuleNodeProperties = (
        GitHubBranchProtectionRuleNodeProperties()
    )
    sub_resource_relationship: GitHubBranchProtectionRuleToRepositoryRel = (
        GitHubBranchProtectionRuleToRepositoryRel()
    )
