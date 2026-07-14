"""
GitLab CI/CD include schema.

Each `include:` entry from a `.gitlab-ci.yml` becomes a GitLabCIInclude node.
The `is_pinned` flag is the security signal: a project include without a SHA
ref is mutable by anyone with push access to the included repo.
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
class GitLabCIIncludeNodeProperties(CartographyNodeProperties):
    """
    Properties for a `.gitlab-ci.yml` include reference.

    `is_pinned` is the primary security signal — a project include without
    a 40-char SHA ref will pull whatever is on the referenced branch / tag
    at pipeline runtime.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Composite identifier formed from the project ID, include type, location, "
            "and ref."
        ),
    )
    include_type: PropertyRef = PropertyRef(
        "include_type",
        extra_index=True,
        description="Include type: local, project, remote, template, or component.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        extra_index=True,
        description="Included path, project path, URL, template name, or component identifier.",
    )
    ref: PropertyRef = PropertyRef(
        "ref",
        description="Commit SHA, tag, or branch used by a project include.",
    )
    is_pinned: PropertyRef = PropertyRef(
        "is_pinned",
        description="Whether the include resolves to an immutable target.",
    )
    is_local: PropertyRef = PropertyRef(
        "is_local",
        description="Whether the include references a file in the same repository.",
    )
    gitlab_url: PropertyRef = PropertyRef(
        "gitlab_url",
        extra_index=True,
        description="URL of the GitLab instance.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GitLabCIConfigUsesIncludeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabCIConfigUsesIncludeRel(CartographyRelSchema):
    """`(:GitLabCIConfig)-[:USES_INCLUDE]->(:GitLabCIInclude)`."""

    target_node_label: str = "GitLabCIConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("config_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES_INCLUDE"
    properties: GitLabCIConfigUsesIncludeRelProperties = (
        GitLabCIConfigUsesIncludeRelProperties()
    )


@dataclass(frozen=True)
class GitLabCIIncludeToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabCIIncludeToProjectRel(CartographyRelSchema):
    """Sub-resource relationship — scoped to GitLabProject."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabCIIncludeToProjectRelProperties = (
        GitLabCIIncludeToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabCIIncludeSchema(CartographyNodeSchema):
    """An include entry referenced by a GitLab CI/CD configuration."""

    label: str = "GitLabCIInclude"
    properties: GitLabCIIncludeNodeProperties = GitLabCIIncludeNodeProperties()
    sub_resource_relationship: GitLabCIIncludeToProjectRel = (
        GitLabCIIncludeToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitLabCIConfigUsesIncludeRel()],
    )
