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
class NotionUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Workspace-scoped Notion user ID.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    notion_user_id: PropertyRef = PropertyRef(
        "notion_user_id",
        extra_index=True,
        description="Notion's user UUID.",
    )
    name: PropertyRef = PropertyRef("name", description="User display name.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="User email when exposed to the connection.",
    )


@dataclass(frozen=True)
class NotionWorkspaceToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NotionWorkspaceToUserRel(CartographyRelSchema):
    """A Notion workspace contains a user account."""

    target_node_label: str = "NotionWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NotionWorkspaceToUserRelProperties = (
        NotionWorkspaceToUserRelProperties()
    )


@dataclass(frozen=True)
class NotionUserSchema(CartographyNodeSchema):
    """A Notion person with the canonical UserAccount label."""

    label: str = "NotionUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: NotionUserNodeProperties = NotionUserNodeProperties()
    sub_resource_relationship: NotionWorkspaceToUserRel = NotionWorkspaceToUserRel()
