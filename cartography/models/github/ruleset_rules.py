"""
Data model for GitHub Ruleset Rules.

Schema for GitHubRulesetRule nodes and their relationships to GitHubRuleset.
Based on GitHub REST API: https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset
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
class GitHubRulesetRuleNodeProperties(CartographyNodeProperties):
    """
    Properties of a GitHubRulesetRule node.
    Maps to a rule in GitHub's repository ruleset REST response.
    """

    id: PropertyRef = PropertyRef("id")
    type: PropertyRef = PropertyRef("type")
    parameters: PropertyRef = PropertyRef("parameters")
    parameters_required_approving_review_count: PropertyRef = PropertyRef(
        "parameters_required_approving_review_count"
    )
    parameters_dismiss_stale_reviews_on_push: PropertyRef = PropertyRef(
        "parameters_dismiss_stale_reviews_on_push"
    )
    parameters_require_code_owner_review: PropertyRef = PropertyRef(
        "parameters_require_code_owner_review"
    )
    parameters_required_status_checks: PropertyRef = PropertyRef(
        "parameters_required_status_checks"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetRuleToRulesetRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between a rule and its ruleset.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetRuleToRulesetRel(CartographyRelSchema):
    """
    Relationship: (GitHubRuleset)-[:CONTAINS_RULE]->(GitHubRulesetRule)
    A ruleset can have multiple rules.
    """

    target_node_label: str = "GitHubRuleset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ruleset_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS_RULE"
    properties: GitHubRulesetRuleToRulesetRelProperties = (
        GitHubRulesetRuleToRulesetRelProperties()
    )


@dataclass(frozen=True)
class GitHubRulesetRuleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetRuleToOrganizationRel(CartographyRelSchema):
    """
    Relationship: (GitHubOrganization)-[:RESOURCE]->(GitHubRulesetRule)
    Used for cleanup - ruleset rules belong to an organization.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubRulesetRuleToOrganizationRelProperties = (
        GitHubRulesetRuleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitHubRulesetRuleSchema(CartographyNodeSchema):
    label: str = "GitHubRulesetRule"
    properties: GitHubRulesetRuleNodeProperties = GitHubRulesetRuleNodeProperties()
    sub_resource_relationship: GitHubRulesetRuleToOrganizationRel = (
        GitHubRulesetRuleToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubRulesetRuleToRulesetRel()]
    )
