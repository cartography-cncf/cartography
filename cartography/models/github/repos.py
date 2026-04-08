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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    createdat: PropertyRef = PropertyRef("createdat")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    fullname: PropertyRef = PropertyRef("fullname")
    description: PropertyRef = PropertyRef("description")
    primarylanguage: PropertyRef = PropertyRef("primarylanguage")
    homepage: PropertyRef = PropertyRef("homepage")
    defaultbranch: PropertyRef = PropertyRef("defaultbranch")
    defaultbranchid: PropertyRef = PropertyRef("defaultbranchid")
    private: PropertyRef = PropertyRef("private")
    disabled: PropertyRef = PropertyRef("disabled")
    archived: PropertyRef = PropertyRef("archived")
    locked: PropertyRef = PropertyRef("locked")
    giturl: PropertyRef = PropertyRef("giturl")
    url: PropertyRef = PropertyRef("url", extra_index=True)
    sshurl: PropertyRef = PropertyRef("sshurl")
    updatedat: PropertyRef = PropertyRef("updatedat")


@dataclass(frozen=True)
class GitHubRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRepositoryToOwnerOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNER"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubRepositoryToOwnerUserRel(CartographyRelSchema):
    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNER"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubRepositorySchema(CartographyNodeSchema):
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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class GitHubBranchToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubBranchToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BRANCH"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubBranchSchema(CartographyNodeSchema):
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
    id: PropertyRef = PropertyRef("language_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("language_name", extra_index=True)


@dataclass(frozen=True)
class ProgrammingLanguageToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LANGUAGE"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class ProgrammingLanguageSchema(CartographyNodeSchema):
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
    id: PropertyRef = PropertyRef("owner_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef("owner", extra_index=True)


@dataclass(frozen=True)
class GitHubOwnerUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("owner_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef("owner", extra_index=True)


@dataclass(frozen=True)
class GitHubOwnerToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubOwnerOrganizationSchema(CartographyNodeSchema):
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
    label: str = "GitHubUser"
    properties: GitHubOwnerUserNodeProperties = GitHubOwnerUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubOwnerToRepositoryRel()],
    )


@dataclass(frozen=True)
class GitHubCollaboratorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    fullname: PropertyRef = PropertyRef("name")
    username: PropertyRef = PropertyRef("login", extra_index=True)
    permission: PropertyRef = PropertyRef("permission")
    email: PropertyRef = PropertyRef("email")
    company: PropertyRef = PropertyRef("company")


@dataclass(frozen=True)
class GitHubCollaboratorToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DIRECT_COLLAB_ADMIN"
    properties: GitHubRepositoryRelProperties = GitHubRepositoryRelProperties()


@dataclass(frozen=True)
class _GitHubCollaboratorSchema(CartographyNodeSchema):
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
class GitHubPythonLibraryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    specifier: PropertyRef = PropertyRef("specifier")
    version: PropertyRef = PropertyRef("version")


@dataclass(frozen=True)
class GitHubPythonLibraryToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    specifier: PropertyRef = PropertyRef("specifier")


@dataclass(frozen=True)
class GitHubPythonLibraryToRepositoryRel(CartographyRelSchema):
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
    return _GitHubCollaboratorSchema(rel_label=rel_label)
