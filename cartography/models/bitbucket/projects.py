"""
Bitbucket Cloud Project Schema

Projects group related repositories together within a workspace.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class BitbucketProjectNodeProperties(CartographyNodeProperties):
    """Properties for a Bitbucket Cloud Project node."""

    id: PropertyRef = PropertyRef(
        "id",
        description="Bitbucket project UUID.",
    )
    key: PropertyRef = PropertyRef(
        "key",
        extra_index=True,
        description="Short project key, unique within the workspace.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Display name of the project.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable description of the project.",
    )
    is_private: PropertyRef = PropertyRef(
        "is_private",
        description="Whether the project is private.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on",
        description="Timestamp when Bitbucket created the project.",
    )
    updated_on: PropertyRef = PropertyRef(
        "updated_on",
        description="Timestamp of the project's most recent update.",
    )
    link_html: PropertyRef = PropertyRef(
        "link_html",
        description="URL for viewing the project in Bitbucket.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BitbucketProjectToWorkspaceRelProperties(CartographyRelProperties):
    """Properties for the RESOURCE relationship between BitbucketWorkspace and BitbucketProject."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BitbucketProjectToWorkspaceRel(CartographyRelSchema):
    """Sub-resource relationship from BitbucketProject to BitbucketWorkspace, used for cleanup scoping."""

    target_node_label: str = "BitbucketWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BitbucketProjectToWorkspaceRelProperties = (
        BitbucketProjectToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class BitbucketProjectSchema(CartographyNodeSchema):
    """A Bitbucket Cloud project, grouping repositories within a workspace."""

    label: str = "BitbucketProject"
    properties: BitbucketProjectNodeProperties = BitbucketProjectNodeProperties()
    sub_resource_relationship: BitbucketProjectToWorkspaceRel = (
        BitbucketProjectToWorkspaceRel()
    )
