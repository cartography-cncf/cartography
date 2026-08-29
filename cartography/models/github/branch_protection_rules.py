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
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubBranchProtectionRuleNodeProperties(CartographyNodeProperties):
    """
    Properties of a GitHubBranchProtectionRule node.
    Maps to GitHub's BranchProtectionRule GraphQL type.
    """

    id: PropertyRef = PropertyRef("id", description="GitHub branch protection rule ID.")
    pattern: PropertyRef = PropertyRef(
        "pattern", description="Branch name pattern protected by the rule."
    )
    allows_deletions: PropertyRef = PropertyRef(
        "allows_deletions", description="Whether matching branches can be deleted."
    )
    allows_force_pushes: PropertyRef = PropertyRef(
        "allows_force_pushes",
        description="Whether matching branches allow force pushes.",
    )
    dismisses_stale_reviews: PropertyRef = PropertyRef(
        "dismisses_stale_reviews",
        description="Whether new commits dismiss stale pull request reviews.",
    )
    is_admin_enforced: PropertyRef = PropertyRef(
        "is_admin_enforced",
        description="Whether repository administrators must follow the rule.",
    )
    requires_approving_reviews: PropertyRef = PropertyRef(
        "requires_approving_reviews",
        description="Whether pull requests require approving reviews.",
    )
    required_approving_review_count: PropertyRef = PropertyRef(
        "required_approving_review_count",
        description="Number of approving reviews required.",
    )
    requires_code_owner_reviews: PropertyRef = PropertyRef(
        "requires_code_owner_reviews",
        description="Whether pull requests require a code owner review.",
    )
    requires_commit_signatures: PropertyRef = PropertyRef(
        "requires_commit_signatures",
        description="Whether matching branches require signed commits.",
    )
    requires_linear_history: PropertyRef = PropertyRef(
        "requires_linear_history",
        description="Whether matching branches require linear history.",
    )
    requires_status_checks: PropertyRef = PropertyRef(
        "requires_status_checks",
        description="Whether required status checks must pass.",
    )
    requires_strict_status_checks: PropertyRef = PropertyRef(
        "requires_strict_status_checks",
        description="Whether branches must be current before status checks pass.",
    )
    restricts_pushes: PropertyRef = PropertyRef(
        "restricts_pushes",
        description="Whether pushes are restricted to selected actors.",
    )
    restricts_review_dismissals: PropertyRef = PropertyRef(
        "restricts_review_dismissals",
        description="Whether review dismissal is restricted to selected actors.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubBranchProtectionRuleToOrganizationRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between a branch protection rule and its organization.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubBranchProtectionRuleToOrganizationRel(CartographyRelSchema):
    """
    Sub-resource relationship: (GitHubOrganization)-[:RESOURCE]->(GitHubBranchProtectionRule).
    Branch protection rules are scoped to the organization for cleanup purposes so
    that a single GraphJob run cleans up rules from every repo in the org.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubBranchProtectionRuleToOrganizationRelProperties = (
        GitHubBranchProtectionRuleToOrganizationRelProperties()
    )


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
        {"id": PropertyRef("repo_url")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULE"
    properties: GitHubBranchProtectionRuleToRepositoryRelProperties = (
        GitHubBranchProtectionRuleToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GitHubBranchProtectionRuleSchema(CartographyNodeSchema):
    """A branch protection rule configured for a GitHub repository."""

    label: str = "GitHubBranchProtectionRule"
    properties: GitHubBranchProtectionRuleNodeProperties = (
        GitHubBranchProtectionRuleNodeProperties()
    )
    sub_resource_relationship: GitHubBranchProtectionRuleToOrganizationRel = (
        GitHubBranchProtectionRuleToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubBranchProtectionRuleToRepositoryRel()]
    )
