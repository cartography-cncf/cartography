from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class NotionWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Stable Notion workspace ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Notion workspace name when exposed to the connection.",
    )
    token_bot_notion_user_id: PropertyRef = PropertyRef(
        "token_bot_notion_user_id",
        description="Notion user UUID of the bot authenticated by this workspace token.",
    )


@dataclass(frozen=True)
class NotionWorkspaceSchema(CartographyNodeSchema):
    """A Notion workspace with the canonical Tenant label."""

    label: str = "NotionWorkspace"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    properties: NotionWorkspaceNodeProperties = NotionWorkspaceNodeProperties()
    scoped_cleanup: bool = False
