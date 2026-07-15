from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="GitHub repository URL.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    createdat: PropertyRef = PropertyRef(
        "createdat", description="Timestamp when the repository was created."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Repository name."
    )
    fullname: PropertyRef = PropertyRef(
        "fullname", description="Repository name in `owner/name` form."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Repository description."
    )
    primarylanguage: PropertyRef = PropertyRef(
        "primarylanguage",
        description="Primary programming language reported by GitHub.",
    )
    homepage: PropertyRef = PropertyRef(
        "homepage", description="Repository homepage URL."
    )
    defaultbranch: PropertyRef = PropertyRef(
        "defaultbranch", description="Default branch name."
    )
    defaultbranchid: PropertyRef = PropertyRef(
        "defaultbranchid", description="GitHub node ID of the default branch."
    )
    private: PropertyRef = PropertyRef(
        "private", description="Whether the repository is private."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether the repository is disabled."
    )
    archived: PropertyRef = PropertyRef(
        "archived", description="Whether the repository is archived."
    )
    locked: PropertyRef = PropertyRef(
        "locked", description="Whether the repository is locked."
    )
    giturl: PropertyRef = PropertyRef(
        "giturl", extra_index=True, description="Repository `git://` clone URL."
    )
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="Repository web URL."
    )
    sshurl: PropertyRef = PropertyRef(
        "sshurl", extra_index=True, description="Repository SSH clone URL."
    )
    updatedat: PropertyRef = PropertyRef(
        "updatedat", description="Timestamp when the repository was last updated."
    )


@dataclass(frozen=True)
class GitHubRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRepositoryToOwnerOrganizationRel(CartographyRelSchema):
    """Links a GitHub repository to its owner."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNER"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubRepositoryToOwnerUserRel(CartographyRelSchema):
    """Links a GitHub repository to its owner."""

    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNER"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubRepositorySchema(CartographyNodeSchema):
    """A source code repository hosted in GitHub."""

    label: str = "GitHubRepository"
    properties: GitHubRepositoryNodeProperties = GitHubRepositoryNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CodeRepository"])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubRepositoryToOwnerOrganizationRel(),
            GitHubRepositoryToOwnerUserRel(),
        ],
    )

    @property
    def scoped_cleanup(self) -> bool:
        return False


@dataclass(frozen=True)
class GitHubBranchNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Repository-qualified GitHub branch identifier."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Branch name.")


@dataclass(frozen=True)
class GitHubBranchToOrganizationRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubBranchToRepositoryRel(CartographyRelSchema):
    """Links a GitHub repository to one of its branches."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BRANCH"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubBranchSchema(CartographyNodeSchema):
    """A branch in a GitHub repository."""

    label: str = "GitHubBranch"
    properties: GitHubBranchNodeProperties = GitHubBranchNodeProperties()
    sub_resource_relationship: GitHubBranchToOrganizationRel = (
        GitHubBranchToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubBranchToRepositoryRel()],
    )


@dataclass(frozen=True)
class ProgrammingLanguageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "language_name", description="Programming language name used as the identifier."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "language_name", extra_index=True, description="Programming language name."
    )


@dataclass(frozen=True)
class ProgrammingLanguageToRepositoryRel(CartographyRelSchema):
    """Links a GitHub repository to a programming language it uses."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LANGUAGE"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class ProgrammingLanguageSchema(CartographyNodeSchema):
    """A programming language used by a GitHub repository."""

    label: str = "ProgrammingLanguage"
    properties: ProgrammingLanguageNodeProperties = ProgrammingLanguageNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [ProgrammingLanguageToRepositoryRel()],
    )

    @property
    def scoped_cleanup(self) -> bool:
        return False


@dataclass(frozen=True)
class GitHubOwnerOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("owner_id", description="GitHub organization URL.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="GitHub organization login."
    )


@dataclass(frozen=True)
class GitHubOwnerUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("owner_id", description="GitHub user profile URL.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="GitHub user login."
    )


@dataclass(frozen=True)
class GitHubOwnerToRepositoryRel(CartographyRelSchema):
    """Links a GitHub repository to its owner."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubOwnerOrganizationSchema(CartographyNodeSchema):
    """An organization in GitHub."""

    label: str = "GitHubOrganization"
    properties: GitHubOwnerOrganizationNodeProperties = (
        GitHubOwnerOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubOwnerToRepositoryRel()],
    )


@dataclass(frozen=True)
class GitHubOwnerUserSchema(CartographyNodeSchema):
    """A user account in GitHub."""

    label: str = "GitHubUser"
    properties: GitHubOwnerUserNodeProperties = GitHubOwnerUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubOwnerToRepositoryRel()],
    )


@dataclass(frozen=True)
class GitHubCollaboratorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("url", description="GitHub user profile URL.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    fullname: PropertyRef = PropertyRef("name", description="GitHub user display name.")
    username: PropertyRef = PropertyRef(
        "login", extra_index=True, description="GitHub user login."
    )
    permission: PropertyRef = PropertyRef(
        "permission", description="Repository permission granted to the collaborator."
    )
    email: PropertyRef = PropertyRef(
        "email", description="Publicly visible profile email."
    )
    company: PropertyRef = PropertyRef("company", description="Public profile company.")


@dataclass(frozen=True)
class GitHubCollaboratorToRepositoryRel(CartographyRelSchema):
    """Grants a direct or outside collaborator the encoded repository permission."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DIRECT_COLLAB_ADMIN"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class _GitHubCollaboratorSchema(CartographyNodeSchema):
    """A user account in GitHub."""

    label: str = "GitHubUser"
    properties: GitHubCollaboratorNodeProperties = GitHubCollaboratorNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    rel_label: str = "DIRECT_COLLAB_ADMIN"

    @property
    def other_relationships(self) -> OtherRelationships:
        return OtherRelationships(
            [GitHubCollaboratorToRepositoryRel(rel_label=self.rel_label)],
        )


@dataclass(frozen=True)
class GitHubDirectCollaboratorAdminSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "DIRECT_COLLAB_ADMIN"


@dataclass(frozen=True)
class GitHubDirectCollaboratorMaintainSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "DIRECT_COLLAB_MAINTAIN"


@dataclass(frozen=True)
class GitHubDirectCollaboratorReadSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "DIRECT_COLLAB_READ"


@dataclass(frozen=True)
class GitHubDirectCollaboratorTriageSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "DIRECT_COLLAB_TRIAGE"


@dataclass(frozen=True)
class GitHubDirectCollaboratorWriteSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "DIRECT_COLLAB_WRITE"


@dataclass(frozen=True)
class GitHubOutsideCollaboratorAdminSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "OUTSIDE_COLLAB_ADMIN"


@dataclass(frozen=True)
class GitHubOutsideCollaboratorMaintainSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "OUTSIDE_COLLAB_MAINTAIN"


@dataclass(frozen=True)
class GitHubOutsideCollaboratorReadSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "OUTSIDE_COLLAB_READ"


@dataclass(frozen=True)
class GitHubOutsideCollaboratorTriageSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "OUTSIDE_COLLAB_TRIAGE"


@dataclass(frozen=True)
class GitHubOutsideCollaboratorWriteSchema(_GitHubCollaboratorSchema):
    """A user account in GitHub."""

    rel_label: str = "OUTSIDE_COLLAB_WRITE"


GITHUB_COLLABORATOR_SCHEMA_TYPES: dict[
    str,
    type[_GitHubCollaboratorSchema],
] = {
    schema_type().rel_label: schema_type
    for schema_type in (
        GitHubDirectCollaboratorAdminSchema,
        GitHubDirectCollaboratorMaintainSchema,
        GitHubDirectCollaboratorReadSchema,
        GitHubDirectCollaboratorTriageSchema,
        GitHubDirectCollaboratorWriteSchema,
        GitHubOutsideCollaboratorAdminSchema,
        GitHubOutsideCollaboratorMaintainSchema,
        GitHubOutsideCollaboratorReadSchema,
        GitHubOutsideCollaboratorTriageSchema,
        GitHubOutsideCollaboratorWriteSchema,
    )
}


@dataclass(frozen=True)
class GitHubPythonLibraryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Canonical package name, optionally combined with an exact version.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Canonical Python package name."
    )
    specifier: PropertyRef = PropertyRef(
        "specifier", description="Version specifier parsed from the requirements file."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Exact Python package version when pinned."
    )


@dataclass(frozen=True)
class GitHubPythonLibraryToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    specifier: PropertyRef = PropertyRef(
        "specifier", description="Python version specifier from the requirements file."
    )


@dataclass(frozen=True)
class GitHubPythonLibraryToRepositoryRel(CartographyRelSchema):
    """Links a GitHub repository to a software dependency it requires."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REQUIRES"
    properties: GitHubPythonLibraryToRepositoryRelProperties = (
        GitHubPythonLibraryToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GitHubPythonLibrarySchema(CartographyNodeSchema):
    """A globally shared Python library required by a GitHub repository."""

    label: str = "PythonLibrary"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Dependency"])
    properties: GitHubPythonLibraryNodeProperties = GitHubPythonLibraryNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubPythonLibraryToRepositoryRel()],
    )

    @property
    def scoped_cleanup(self) -> bool:
        return False


def make_github_collaborator_schema(rel_label: str) -> CartographyNodeSchema:
    schema_type = GITHUB_COLLABORATOR_SCHEMA_TYPES.get(rel_label)
    if schema_type is not None:
        return schema_type()
    return _GitHubCollaboratorSchema(rel_label=rel_label)
