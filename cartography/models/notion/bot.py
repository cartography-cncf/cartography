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
from cartography.models.ontology.labels import THIRD_PARTY_APP


@dataclass(frozen=True)
class NotionBotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Workspace-scoped Notion bot ID.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    notion_user_id: PropertyRef = PropertyRef(
        "notion_user_id",
        extra_index=True,
        description="Notion's bot user UUID.",
    )
    name: PropertyRef = PropertyRef("name", description="Bot display name.")
    owner_type: PropertyRef = PropertyRef(
        "owner_type",
        description="Whether the bot is owned by a workspace or user.",
    )
    owner_notion_user_id: PropertyRef = PropertyRef(
        "owner_notion_user_id",
        description="Notion user UUID of the bot owner when available.",
    )


@dataclass(frozen=True)
class NotionWorkspaceToBotRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NotionWorkspaceToBotRel(CartographyRelSchema):
    """A Notion workspace contains a bot connection."""

    target_node_label: str = "NotionWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NotionWorkspaceToBotRelProperties = NotionWorkspaceToBotRelProperties()


@dataclass(frozen=True)
class NotionBotToOwnerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NotionBotToOwnerRel(CartographyRelSchema):
    """A Notion bot is owned by a Notion user when Notion exposes one."""

    target_node_label: str = "NotionUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: NotionBotToOwnerRelProperties = NotionBotToOwnerRelProperties()


@dataclass(frozen=True)
class NotionBotSchema(CartographyNodeSchema):
    """A Notion bot connection with the canonical ThirdPartyApp label."""

    label: str = "NotionBot"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([THIRD_PARTY_APP])
    properties: NotionBotNodeProperties = NotionBotNodeProperties()
    sub_resource_relationship: NotionWorkspaceToBotRel = NotionWorkspaceToBotRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [NotionBotToOwnerRel()],
    )
