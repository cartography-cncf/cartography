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
class GitLabRepositoryNodeProperties(CartographyNodeProperties):
    """Properties for a GitLab repository (project)."""

    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    numeric_id: PropertyRef = PropertyRef("numeric_id", extra_index=True)
    # Core identification
    name: PropertyRef = PropertyRef("name")
    path: PropertyRef = PropertyRef("path")
    path_with_namespace: PropertyRef = PropertyRef("path_with_namespace")
    # URLs
    web_url: PropertyRef = PropertyRef("web_url")
    http_url_to_repo: PropertyRef = PropertyRef("http_url_to_repo")
    ssh_url_to_repo: PropertyRef = PropertyRef("ssh_url_to_repo")
    readme_url: PropertyRef = PropertyRef("readme_url")
    # Metadata
    description: PropertyRef = PropertyRef("description")
    visibility: PropertyRef = PropertyRef("visibility")
    archived: PropertyRef = PropertyRef("archived")
    default_branch: PropertyRef = PropertyRef("default_branch")
    # Stats
    star_count: PropertyRef = PropertyRef("star_count")
    forks_count: PropertyRef = PropertyRef("forks_count")
    open_issues_count: PropertyRef = PropertyRef("open_issues_count")
    # Timestamps
    created_at: PropertyRef = PropertyRef("created_at")
    last_activity_at: PropertyRef = PropertyRef("last_activity_at")
    # Features
    issues_enabled: PropertyRef = PropertyRef("issues_enabled")
    merge_requests_enabled: PropertyRef = PropertyRef("merge_requests_enabled")
    wiki_enabled: PropertyRef = PropertyRef("wiki_enabled")
    snippets_enabled: PropertyRef = PropertyRef("snippets_enabled")
    container_registry_enabled: PropertyRef = PropertyRef("container_registry_enabled")
    # Access
    empty_repo: PropertyRef = PropertyRef("empty_repo")


@dataclass(frozen=True)
class GitLabRepositoryToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabRepositoryToGroupRel(CartographyRelSchema):
    """Relationship from GitLabGroup to GitLabRepository (OWNER)."""

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER"
    properties: GitLabRepositoryToGroupRelProperties = (
        GitLabRepositoryToGroupRelProperties()
    )


@dataclass(frozen=True)
class GitLabRepositorySchema(CartographyNodeSchema):
    label: str = "GitLabRepository"
    properties: GitLabRepositoryNodeProperties = GitLabRepositoryNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            GitLabRepositoryToGroupRel(),
        ],
    )

    @property
    def scoped_cleanup(self) -> bool:
        return False
