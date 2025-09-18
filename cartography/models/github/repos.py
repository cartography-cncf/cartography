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
class GitHubRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
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
    url: PropertyRef = PropertyRef("url")
    sshurl: PropertyRef = PropertyRef("sshurl")
    updatedat: PropertyRef = PropertyRef("updatedat")
    owner_org_id: PropertyRef = PropertyRef("owner_org_id", set_in_kwargs=True)
    owner_user_id: PropertyRef = PropertyRef("owner_user_id", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRepositoryToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRepositoryToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubRepositoryToOrganizationRelProperties = (
        GitHubRepositoryToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitHubRepositoryToOwnerOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRepositoryToOwnerOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNER"
    properties: GitHubRepositoryToOwnerOrganizationRelProperties = (
        GitHubRepositoryToOwnerOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitHubRepositoryToOwnerUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRepositoryToOwnerUserRel(CartographyRelSchema):
    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNER"
    properties: GitHubRepositoryToOwnerUserRelProperties = (
        GitHubRepositoryToOwnerUserRelProperties()
    )


@dataclass(frozen=True)
class GitHubRepositorySchema(CartographyNodeSchema):
    label: str = "GitHubRepository"
    properties: GitHubRepositoryNodeProperties = GitHubRepositoryNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubRepositoryToOwnerOrganizationRel(),
            GitHubRepositoryToOwnerUserRel(),
        ],
    )
    sub_resource_relationship: GitHubRepositoryToOrganizationRel = (
        GitHubRepositoryToOrganizationRel()
    )


@dataclass(frozen=True)
class GitHubBranchNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    repo_id: PropertyRef = PropertyRef("repo_id", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubBranchToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubBranchToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BRANCH"
    properties: GitHubBranchToRepositoryRelProperties = (
        GitHubBranchToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GitHubBranchSchema(CartographyNodeSchema):
    label: str = "GitHubBranch"
    properties: GitHubBranchNodeProperties = GitHubBranchNodeProperties()
    sub_resource_relationship: GitHubBranchToRepositoryRel = (
        GitHubBranchToRepositoryRel()
    )
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class ProgrammingLanguageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    repo_id: PropertyRef = PropertyRef("repo_id", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProgrammingLanguageToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProgrammingLanguageToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LANGUAGE"
    properties: ProgrammingLanguageToRepositoryRelProperties = (
        ProgrammingLanguageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class ProgrammingLanguageSchema(CartographyNodeSchema):
    label: str = "ProgrammingLanguage"
    properties: ProgrammingLanguageNodeProperties = ProgrammingLanguageNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [ProgrammingLanguageToRepositoryRel()],
    )
    sub_resource_relationship = None
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class GitHubRepositoryOwnerUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    username: PropertyRef = PropertyRef("login", extra_index=True)
    fullname: PropertyRef = PropertyRef("name")
    email: PropertyRef = PropertyRef("email")
    company: PropertyRef = PropertyRef("company")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRepositoryOwnerUserSchema(CartographyNodeSchema):
    label: str = "GitHubUser"
    properties: GitHubRepositoryOwnerUserNodeProperties = (
        GitHubRepositoryOwnerUserNodeProperties()
    )
    sub_resource_relationship = None
    other_relationships = None
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class GitHubCollaboratorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubUserToRepoDirectAdminRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "direct_collab_admin_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DIRECT_COLLAB_ADMIN"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoDirectMaintainRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "direct_collab_maintain_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DIRECT_COLLAB_MAINTAIN"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoDirectReadRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "direct_collab_read_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DIRECT_COLLAB_READ"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoDirectTriageRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "direct_collab_triage_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DIRECT_COLLAB_TRIAGE"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoDirectWriteRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "direct_collab_write_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DIRECT_COLLAB_WRITE"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoOutsideAdminRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "outside_collab_admin_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OUTSIDE_COLLAB_ADMIN"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoOutsideMaintainRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "outside_collab_maintain_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OUTSIDE_COLLAB_MAINTAIN"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoOutsideReadRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "outside_collab_read_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OUTSIDE_COLLAB_READ"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoOutsideTriageRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "outside_collab_triage_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OUTSIDE_COLLAB_TRIAGE"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubUserToRepoOutsideWriteRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "outside_collab_write_repo_ids",
                one_to_many=True,
                set_in_kwargs=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OUTSIDE_COLLAB_WRITE"
    properties: GitHubCollaboratorRelProperties = GitHubCollaboratorRelProperties()


@dataclass(frozen=True)
class GitHubRepositoryCollaboratorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    username: PropertyRef = PropertyRef("login", extra_index=True)
    fullname: PropertyRef = PropertyRef("name")
    email: PropertyRef = PropertyRef("email")
    company: PropertyRef = PropertyRef("company")
    direct_collab_admin_repo_ids: PropertyRef = PropertyRef(
        "direct_collab_admin_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    direct_collab_maintain_repo_ids: PropertyRef = PropertyRef(
        "direct_collab_maintain_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    direct_collab_read_repo_ids: PropertyRef = PropertyRef(
        "direct_collab_read_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    direct_collab_triage_repo_ids: PropertyRef = PropertyRef(
        "direct_collab_triage_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    direct_collab_write_repo_ids: PropertyRef = PropertyRef(
        "direct_collab_write_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    outside_collab_admin_repo_ids: PropertyRef = PropertyRef(
        "outside_collab_admin_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    outside_collab_maintain_repo_ids: PropertyRef = PropertyRef(
        "outside_collab_maintain_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    outside_collab_read_repo_ids: PropertyRef = PropertyRef(
        "outside_collab_read_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    outside_collab_triage_repo_ids: PropertyRef = PropertyRef(
        "outside_collab_triage_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    outside_collab_write_repo_ids: PropertyRef = PropertyRef(
        "outside_collab_write_repo_ids",
        one_to_many=True,
        set_in_kwargs=True,
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubRepositoryCollaboratorSchema(CartographyNodeSchema):
    label: str = "GitHubUser"
    properties: GitHubRepositoryCollaboratorNodeProperties = (
        GitHubRepositoryCollaboratorNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubUserToRepoDirectAdminRel(),
            GitHubUserToRepoDirectMaintainRel(),
            GitHubUserToRepoDirectReadRel(),
            GitHubUserToRepoDirectTriageRel(),
            GitHubUserToRepoDirectWriteRel(),
            GitHubUserToRepoOutsideAdminRel(),
            GitHubUserToRepoOutsideMaintainRel(),
            GitHubUserToRepoOutsideReadRel(),
            GitHubUserToRepoOutsideTriageRel(),
            GitHubUserToRepoOutsideWriteRel(),
        ],
    )
    sub_resource_relationship = None
    scoped_cleanup: bool = False
