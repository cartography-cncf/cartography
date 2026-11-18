"""
Bitbucket Cloud Repository Schema

Repositories always belong to a workspace, and optionally to a project within it.
"""

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
from cartography.models.ontology.labels import CODE_REPOSITORY


@dataclass(frozen=True)
class BitbucketRepositoryNodeProperties(CartographyNodeProperties):
    """Properties for a Bitbucket Cloud Repository node."""

    id: PropertyRef = PropertyRef(
        "id",
        description="Bitbucket repository UUID.",
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        extra_index=True,
        description="Repository full name, in the form workspace/repo_slug.",
    )
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="URL-friendly repository identifier.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Display name of the repository.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable description of the repository.",
    )
    is_private: PropertyRef = PropertyRef(
        "is_private",
        description="Whether the repository is private.",
    )
    scm: PropertyRef = PropertyRef(
        "scm",
        description="Source control system used by the repository, e.g. git.",
    )
    mainbranch_name: PropertyRef = PropertyRef(
        "mainbranch_name",
        description="Name of the repository's main branch.",
    )
    project_key: PropertyRef = PropertyRef(
        "project_key",
        description="Key of the Bitbucket project this repository belongs to, if any.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on",
        description="Timestamp when Bitbucket created the repository.",
    )
    updated_on: PropertyRef = PropertyRef(
        "updated_on",
        description="Timestamp of the repository's most recent update.",
    )
    size: PropertyRef = PropertyRef(
        "size",
        description="Repository size in bytes.",
    )
    language: PropertyRef = PropertyRef(
        "language",
        description="Primary programming language detected by Bitbucket.",
    )
    clone_https: PropertyRef = PropertyRef(
        "clone_https",
        description="HTTPS clone URL for the repository.",
    )
    clone_ssh: PropertyRef = PropertyRef(
        "clone_ssh",
        description="SSH clone URL for the repository.",
    )
    link_html: PropertyRef = PropertyRef(
        "link_html",
        description="URL for viewing the repository in Bitbucket.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BitbucketRepositoryToWorkspaceRelProperties(CartographyRelProperties):
    """Properties for the RESOURCE relationship between BitbucketWorkspace and BitbucketRepository."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BitbucketRepositoryToWorkspaceRel(CartographyRelSchema):
    """
    Sub-resource relationship from BitbucketRepository to BitbucketWorkspace.
    Repositories always belong to a workspace, even without a project, so the
    workspace is the cleanup-scoping root.
    """

    target_node_label: str = "BitbucketWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BitbucketRepositoryToWorkspaceRelProperties = (
        BitbucketRepositoryToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class BitbucketRepositoryToProjectRelProperties(CartographyRelProperties):
    """Properties for the CONTAINS relationship between BitbucketProject and BitbucketRepository."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BitbucketRepositoryToProjectRel(CartographyRelSchema):
    """
    Relationship from BitbucketRepository to BitbucketProject via CONTAINS.
    Only created when a repository has a project assigned - repos with no
    project simply omit the "project_id" key on their record.
    """

    target_node_label: str = "BitbucketProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: BitbucketRepositoryToProjectRelProperties = (
        BitbucketRepositoryToProjectRelProperties()
    )


@dataclass(frozen=True)
class BitbucketRepositorySchema(CartographyNodeSchema):
    """
    A Bitbucket Cloud repository.

    Every repository belongs to a workspace. Repositories also belong to a
    project, except legacy repositories created before Bitbucket introduced
    projects. Per-repository permissions, pull requests, and branch
    restrictions aren't ingested.
    """

    label: str = "BitbucketRepository"
    properties: BitbucketRepositoryNodeProperties = BitbucketRepositoryNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CODE_REPOSITORY])
    sub_resource_relationship: BitbucketRepositoryToWorkspaceRel = (
        BitbucketRepositoryToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            BitbucketRepositoryToProjectRel(),
        ],
    )
