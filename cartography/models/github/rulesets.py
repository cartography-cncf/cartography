"""
Data model for GitHub Repository Rulesets.

Schema for GitHubRuleset nodes and their relationships to GitHubRepository.
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
class GitHubRulesetNodeProperties(CartographyNodeProperties):
    """
    Properties of a GitHubRuleset node.
    Maps to GitHub's repository ruleset REST response.
    """

    id: PropertyRef = PropertyRef("id", description="GitHub ruleset node ID.")
    database_id: PropertyRef = PropertyRef(
        "database_id", description="GitHub numeric database ID for the ruleset."
    )
    name: PropertyRef = PropertyRef("name", description="Ruleset name.")
    target: PropertyRef = PropertyRef(
        "target", description="Ruleset target, such as `BRANCH` or `TAG`."
    )
    enforcement: PropertyRef = PropertyRef(
        "enforcement", description="Ruleset enforcement mode."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the ruleset was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the ruleset was last updated."
    )
    conditions_ref_name_include: PropertyRef = PropertyRef(
        "conditions_ref_name_include",
        description="Ref name patterns included by the ruleset.",
    )
    conditions_ref_name_exclude: PropertyRef = PropertyRef(
        "conditions_ref_name_exclude",
        description="Ref name patterns excluded by the ruleset.",
    )
    conditions_repository_name_include: PropertyRef = PropertyRef(
        "conditions_repository_name_include",
        description="Repository name patterns included by the ruleset.",
    )
    conditions_repository_name_exclude: PropertyRef = PropertyRef(
        "conditions_repository_name_exclude",
        description="Repository name patterns excluded by the ruleset.",
    )
    conditions_repository_name_protected: PropertyRef = PropertyRef(
        "conditions_repository_name_protected",
        description="Whether repository-name conditions select protected repositories.",
    )
    conditions_repository_ids: PropertyRef = PropertyRef(
        "conditions_repository_ids",
        description="Repository database IDs selected by the ruleset.",
    )
    conditions_repository_property_include: PropertyRef = PropertyRef(
        "conditions_repository_property_include",
        description="Repository property include conditions encoded as JSON.",
    )
    conditions_repository_property_exclude: PropertyRef = PropertyRef(
        "conditions_repository_property_exclude",
        description="Repository property exclude conditions encoded as JSON.",
    )
    conditions_organization_property_include: PropertyRef = PropertyRef(
        "conditions_organization_property_include",
        description="Organization property include conditions encoded as JSON.",
    )
    conditions_organization_property_exclude: PropertyRef = PropertyRef(
        "conditions_organization_property_exclude",
        description="Organization property exclude conditions encoded as JSON.",
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
        {"id": PropertyRef("repo_url")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULESET"
    properties: GitHubRulesetToRepositoryRelProperties = (
        GitHubRulesetToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GitHubRulesetToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetToOrganizationRel(CartographyRelSchema):
    """
    Relationship: (GitHubOrganization)-[:RESOURCE]->(GitHubRuleset)
    Used for cleanup - rulesets belong to an organization.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubRulesetToOrganizationRelProperties = (
        GitHubRulesetToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitHubRulesetSchema(CartographyNodeSchema):
    """A repository ruleset configured in GitHub."""

    label: str = "GitHubRuleset"
    properties: GitHubRulesetNodeProperties = GitHubRulesetNodeProperties()
    sub_resource_relationship: GitHubRulesetToOrganizationRel = (
        GitHubRulesetToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubRulesetToRepositoryRel()]
    )
