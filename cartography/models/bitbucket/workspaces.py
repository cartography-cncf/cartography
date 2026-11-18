"""
Bitbucket Cloud Workspace Schema

A workspace is the top-level container in Bitbucket Cloud that holds projects,
repositories, and members.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class BitbucketWorkspaceNodeProperties(CartographyNodeProperties):
    """Properties for a Bitbucket Cloud Workspace node."""

    id: PropertyRef = PropertyRef(
        "id",
        description="Bitbucket workspace UUID.",
    )
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="URL-friendly workspace identifier.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Display name of the workspace.",
    )
    is_private: PropertyRef = PropertyRef(
        "is_private",
        description="Whether the workspace is private.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on",
        description="Timestamp when Bitbucket created the workspace.",
    )
    link_html: PropertyRef = PropertyRef(
        "link_html",
        description="URL for viewing the workspace in Bitbucket.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BitbucketWorkspaceSchema(CartographyNodeSchema):
    """
    A Bitbucket Cloud workspace, the tenant boundary for projects, repositories,
    and members.

    Cartography syncs only the workspaces listed in `--bitbucket-workspaces`.
    If you remove a workspace from that list, its node and children stay in
    the graph.
    """

    label: str = "BitbucketWorkspace"
    properties: BitbucketWorkspaceNodeProperties = BitbucketWorkspaceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    # No sub_resource_relationship - workspaces are top-level resources.
