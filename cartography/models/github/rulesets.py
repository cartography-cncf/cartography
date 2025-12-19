"""
Data model for GitHub Repository Rulesets.

Schema for GitHubRuleset nodes and their relationships to GitHubRepository.
Based on GitHub GraphQL API: https://docs.github.com/en/graphql/reference/objects#repositoryruleset
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
class GitHubRulesetNodeProperties(CartographyNodeProperties):
    """
    Properties of a GitHubRuleset node.
    Maps to GitHub's RepositoryRuleset GraphQL type.
    """

    id: PropertyRef = PropertyRef("id")
    database_id: PropertyRef = PropertyRef("database_id")
    name: PropertyRef = PropertyRef("name")
    target: PropertyRef = PropertyRef("target")
    enforcement: PropertyRef = PropertyRef("enforcement")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    conditions_ref_name_include: PropertyRef = PropertyRef(
        "conditions_ref_name_include"
    )
    conditions_ref_name_exclude: PropertyRef = PropertyRef(
        "conditions_ref_name_exclude"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetToRepositoryRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between a ruleset and its repository.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetToRepositoryRel(CartographyRelSchema):
    """
    Relationship: (GitHubRepository)-[:HAS_RULESET]->(GitHubRuleset)
    A repository can have multiple rulesets.
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULESET"
    properties: GitHubRulesetToRepositoryRelProperties = (
        GitHubRulesetToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GitHubRulesetSchema(CartographyNodeSchema):
    label: str = "GitHubRuleset"
    properties: GitHubRulesetNodeProperties = GitHubRulesetNodeProperties()
    sub_resource_relationship: GitHubRulesetToRepositoryRel = (
        GitHubRulesetToRepositoryRel()
    )
