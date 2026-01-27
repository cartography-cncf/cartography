"""
Data model for GitHub Ruleset Rules.

Schema for GitHubRulesetRule nodes and their relationships to GitHubRuleset.
Based on GitHub GraphQL API: https://docs.github.com/en/graphql/reference/objects#repositoryrule
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
    Maps to GitHub's RepositoryRule GraphQL type.
    """

    id: PropertyRef = PropertyRef("id")
    type: PropertyRef = PropertyRef("type")
    parameters: PropertyRef = PropertyRef("parameters")
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
        {"id": PropertyRef("ruleset_id", set_in_kwargs=True)}
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
        {"id": PropertyRef("org_url", set_in_kwargs=True)}
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
