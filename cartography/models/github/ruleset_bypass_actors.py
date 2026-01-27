"""
Data model for GitHub Ruleset Bypass Actors.

Schema for GitHubRulesetBypassActor nodes and their relationships to GitHubRuleset.
Based on GitHub GraphQL API: https://docs.github.com/en/graphql/reference/objects#repositoryrulesetbypassactor
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
class GitHubRulesetBypassActorNodeProperties(CartographyNodeProperties):
    """
    Properties of a GitHubRulesetBypassActor node.
    Maps to GitHub's RepositoryRulesetBypassActor GraphQL type.
    """

    id: PropertyRef = PropertyRef("id")
    bypass_mode: PropertyRef = PropertyRef("bypass_mode")
    actor_type: PropertyRef = PropertyRef("actor_type")
    actor_id: PropertyRef = PropertyRef("actor_id")
    actor_database_id: PropertyRef = PropertyRef("actor_database_id")
    actor_name: PropertyRef = PropertyRef("actor_name")
    actor_slug: PropertyRef = PropertyRef("actor_slug")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetBypassActorToRulesetRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between a bypass actor and its ruleset.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetBypassActorToRulesetRel(CartographyRelSchema):
    """
    Relationship: (GitHubRuleset)-[:ALLOWS_BYPASS]->(GitHubRulesetBypassActor)
    A ruleset can have multiple bypass actors.
    """

    target_node_label: str = "GitHubRuleset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ruleset_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ALLOWS_BYPASS"
    properties: GitHubRulesetBypassActorToRulesetRelProperties = (
        GitHubRulesetBypassActorToRulesetRelProperties()
    )


@dataclass(frozen=True)
class GitHubRulesetBypassActorToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRulesetBypassActorToOrganizationRel(CartographyRelSchema):
    """
    Relationship: (GitHubOrganization)-[:RESOURCE]->(GitHubRulesetBypassActor)
    Used for cleanup - bypass actors belong to an organization.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubRulesetBypassActorToOrganizationRelProperties = (
        GitHubRulesetBypassActorToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitHubRulesetBypassActorSchema(CartographyNodeSchema):
    label: str = "GitHubRulesetBypassActor"
    properties: GitHubRulesetBypassActorNodeProperties = (
        GitHubRulesetBypassActorNodeProperties()
    )
    sub_resource_relationship: GitHubRulesetBypassActorToOrganizationRel = (
        GitHubRulesetBypassActorToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubRulesetBypassActorToRulesetRel()]
    )
