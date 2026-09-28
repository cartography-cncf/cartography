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
class DatabricksRepoNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the repo."
    )
    repo_id: PropertyRef = PropertyRef(
        "repo_id", extra_index=True, description="Databricks repo identifier."
    )
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="Remote Git repository URL."
    )
    provider: PropertyRef = PropertyRef(
        "provider", description="Git provider hosting the remote repository."
    )
    branch: PropertyRef = PropertyRef(
        "branch", description="Git branch checked out in the repo."
    )
    head_commit_id: PropertyRef = PropertyRef(
        "head_commit_id", description="Commit identifier currently checked out."
    )
    path: PropertyRef = PropertyRef(
        "path", extra_index=True, description="Workspace path of the repo."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksRepoToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksRepo)
class DatabricksRepoToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the repo as a resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksRepoToWorkspaceRelProperties = (
        DatabricksRepoToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksRepoToGitHubRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksRepo)-[:SOURCED_FROM]->(:GitHubRepository)
class DatabricksRepoToGitHubRepositoryRel(CartographyRelSchema):
    """A Databricks repo is sourced from a GitHub repository."""

    target_node_label: str = "GitHubRepository"
    # ``github_url`` is the repo URL with a trailing ``.git`` trimmed, matching
    # the GitHubRepository html url; the edge forms only when that repo has been
    # ingested by the github module (code-to-cloud correlation).
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"url": PropertyRef("github_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SOURCED_FROM"
    properties: DatabricksRepoToGitHubRepositoryRelProperties = (
        DatabricksRepoToGitHubRepositoryRelProperties()
    )


@dataclass(frozen=True)
class DatabricksRepoSchema(CartographyNodeSchema):
    """A Git repository checked out in a Databricks workspace."""

    label: str = "DatabricksRepo"
    properties: DatabricksRepoNodeProperties = DatabricksRepoNodeProperties()
    sub_resource_relationship: DatabricksRepoToWorkspaceRel = (
        DatabricksRepoToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksRepoToGitHubRepositoryRel()],
    )
