"""
Bitbucket Cloud User Schema

Users are members of a workspace.
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
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class BitbucketUserNodeProperties(CartographyNodeProperties):
    """Properties for a Bitbucket Cloud workspace member."""

    id: PropertyRef = PropertyRef(
        "account_id",
        description="Stable Atlassian account ID for the user.",
    )
    uuid: PropertyRef = PropertyRef(
        "uuid",
        extra_index=True,
        description="Bitbucket user UUID.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        extra_index=True,
        description="Display name of the user.",
    )
    nickname: PropertyRef = PropertyRef(
        "nickname",
        description="Nickname of the user.",
    )
    avatar_url: PropertyRef = PropertyRef(
        "avatar_url",
        description="URL of the user's avatar image.",
    )
    link_html: PropertyRef = PropertyRef(
        "link_html",
        description="URL for viewing the user's profile in Bitbucket.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BitbucketUserToWorkspaceRelProperties(CartographyRelProperties):
    """Properties for the RESOURCE relationship between BitbucketWorkspace and BitbucketUser."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BitbucketUserToWorkspaceRel(CartographyRelSchema):
    """Sub-resource relationship from BitbucketUser to BitbucketWorkspace, used for cleanup scoping."""

    target_node_label: str = "BitbucketWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BitbucketUserToWorkspaceRelProperties = (
        BitbucketUserToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class BitbucketUserSchema(CartographyNodeSchema):
    """
    A current member of a Bitbucket Cloud workspace.

    `id` is the Atlassian account ID, so a user who belongs to several synced
    workspaces is one node with a `RESOURCE` relationship from each workspace.
    Cartography doesn't map which users can access which repositories.

    If Cartography can't list the members of any workspace in a run, it skips
    `BitbucketUser` cleanup for every workspace in that run. Sync all of your
    workspaces in a single run: when workspaces sync in separate runs, removing
    a user from one workspace also removes the node and its other workspace
    memberships until those workspaces sync again.
    """

    label: str = "BitbucketUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: BitbucketUserNodeProperties = BitbucketUserNodeProperties()
    sub_resource_relationship: BitbucketUserToWorkspaceRel = (
        BitbucketUserToWorkspaceRel()
    )
