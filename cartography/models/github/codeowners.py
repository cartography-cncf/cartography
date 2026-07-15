from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubCodeOwnerRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Stable identifier derived from repository, source path, line, "
            "pattern, and owners."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    repo_url: PropertyRef = PropertyRef(
        "repo_url", extra_index=True, description="URL of the containing repository."
    )
    repo_name: PropertyRef = PropertyRef(
        "repo_name", description="Name of the containing repository."
    )
    default_branch: PropertyRef = PropertyRef(
        "default_branch", description="Default branch used to locate CODEOWNERS."
    )
    source_path: PropertyRef = PropertyRef(
        "source_path", description="Path of the effective CODEOWNERS file."
    )
    line_number: PropertyRef = PropertyRef(
        "line_number", description="Line number in the CODEOWNERS file."
    )
    pattern: PropertyRef = PropertyRef(
        "pattern", description="Path pattern parsed from the CODEOWNERS rule."
    )
    owners: PropertyRef = PropertyRef(
        "owners", description="Raw owner tokens parsed from the CODEOWNERS rule."
    )
    owner_logins: PropertyRef = PropertyRef(
        "owner_logins", description="GitHub user logins parsed from `@user` owners."
    )
    owner_team_slugs: PropertyRef = PropertyRef(
        "owner_team_slugs",
        description="GitHub team slugs parsed from `@organization/team` owners.",
    )
    owner_emails: PropertyRef = PropertyRef(
        "owner_emails", description="Email addresses parsed from owner tokens."
    )
    unresolved_owners: PropertyRef = PropertyRef(
        "unresolved_owners",
        description="Owner tokens that could not be classified as users, teams, or emails.",
    )


@dataclass(frozen=True)
class GitHubCodeOwnerRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubCodeOwnerRuleToOrganizationRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubCodeOwnerRuleRelProperties = GitHubCodeOwnerRuleRelProperties()


@dataclass(frozen=True)
class GitHubRepositoryToCodeOwnerRuleRel(CartographyRelSchema):
    """Defines the `HAS_CODEOWNER_RULE` relationship between GitHub resources."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CODEOWNER_RULE"
    properties: GitHubCodeOwnerRuleRelProperties = GitHubCodeOwnerRuleRelProperties()


@dataclass(frozen=True)
class GitHubCodeOwnerRuleToTeamRel(CartographyRelSchema):
    """Links a CODEOWNERS rule to a resolved GitHub user or team."""

    target_node_label: str = "GitHubTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CODEOWNER"
    properties: GitHubCodeOwnerRuleRelProperties = GitHubCodeOwnerRuleRelProperties()


@dataclass(frozen=True)
class GitHubCodeOwnerRuleToUserRel(CartographyRelSchema):
    """Links a CODEOWNERS rule to a resolved GitHub user or team."""

    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CODEOWNER"
    properties: GitHubCodeOwnerRuleRelProperties = GitHubCodeOwnerRuleRelProperties()


@dataclass(frozen=True)
class GitHubCodeOwnerRuleSchema(CartographyNodeSchema):
    """A supported rule parsed from the effective CODEOWNERS file on a repository default branch."""

    label: str = "GitHubCodeOwnerRule"
    properties: GitHubCodeOwnerRuleNodeProperties = GitHubCodeOwnerRuleNodeProperties()
    sub_resource_relationship: GitHubCodeOwnerRuleToOrganizationRel = (
        GitHubCodeOwnerRuleToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubRepositoryToCodeOwnerRuleRel(),
            GitHubCodeOwnerRuleToTeamRel(),
            GitHubCodeOwnerRuleToUserRel(),
        ]
    )


@dataclass(frozen=True)
class DependencyGraphManifestToCodeOwnerRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    matched_path: PropertyRef = PropertyRef(
        "matched_path",
        description="Repository-relative path matched by the CODEOWNERS rule.",
    )
    match_pattern: PropertyRef = PropertyRef(
        "match_pattern", description="CODEOWNERS pattern that matched the path."
    )


@dataclass(frozen=True)
class DependencyGraphManifestToCodeOwnerRuleMatchLink(CartographyRelSchema):
    """Links a dependency manifest path to its effective CODEOWNERS rule."""

    target_node_label: str = "GitHubCodeOwnerRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("rule_id")}
    )
    source_node_label: str = "GitHubDependencyGraphManifest"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("manifest_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MATCHES_CODEOWNER_RULE"
    properties: DependencyGraphManifestToCodeOwnerRuleRelProperties = (
        DependencyGraphManifestToCodeOwnerRuleRelProperties()
    )
