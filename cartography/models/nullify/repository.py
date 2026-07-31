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
class NullifyRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Canonical repository identifier that findings and teams reference.
    repository_id: PropertyRef = PropertyRef("repositoryId", extra_index=True)
    name: PropertyRef = PropertyRef("repository", extra_index=True)
    owner: PropertyRef = PropertyRef("owner")
    owner_type: PropertyRef = PropertyRef("ownerType")
    platform: PropertyRef = PropertyRef("platform")
    language: PropertyRef = PropertyRef("language")
    default_branch: PropertyRef = PropertyRef("defaultBranch")
    default_branch_committed_at: PropertyRef = PropertyRef("defaultBranchCommittedAt")
    is_archived: PropertyRef = PropertyRef("isArchived")
    is_enrolled: PropertyRef = PropertyRef("isEnrolled")


@dataclass(frozen=True)
class NullifyRepositoryToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTenant)-[:RESOURCE]->(:NullifyRepository)
class NullifyRepositoryToTenantRel(CartographyRelSchema):
    target_node_label: str = "NullifyTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NullifyRepositoryToTenantRelProperties = (
        NullifyRepositoryToTenantRelProperties()
    )


@dataclass(frozen=True)
class NullifyRepositoryToGitHubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyRepository)-[:MIRRORS]->(:GitHubRepository)
class NullifyRepositoryToGitHubRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    # Match key derived in transform() from platform + owner + name.
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("_github_fullname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MIRRORS"
    properties: NullifyRepositoryToGitHubRepoRelProperties = (
        NullifyRepositoryToGitHubRepoRelProperties()
    )


@dataclass(frozen=True)
class NullifyRepositoryToGitLabProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyRepository)-[:MIRRORS]->(:GitLabProject)
class NullifyRepositoryToGitLabProjectRel(CartographyRelSchema):
    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("_gitlab_web_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MIRRORS"
    properties: NullifyRepositoryToGitLabProjectRelProperties = (
        NullifyRepositoryToGitLabProjectRelProperties()
    )


@dataclass(frozen=True)
class NullifyRepositorySchema(CartographyNodeSchema):
    label: str = "NullifyRepository"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Asset"])
    properties: NullifyRepositoryNodeProperties = NullifyRepositoryNodeProperties()
    sub_resource_relationship: NullifyRepositoryToTenantRel = (
        NullifyRepositoryToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NullifyRepositoryToGitHubRepoRel(),
            NullifyRepositoryToGitLabProjectRel(),
        ],
    )
