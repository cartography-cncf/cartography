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
class NotionPageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Workspace-scoped Notion page ID.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    notion_page_id: PropertyRef = PropertyRef(
        "notion_page_id",
        extra_index=True,
        description="Notion's page UUID.",
    )
    title: PropertyRef = PropertyRef(
        "title",
        description="Page title when exposed to the connection.",
    )
    url: PropertyRef = PropertyRef(
        "url",
        description="Private Notion application URL for the page.",
    )
    public_url: PropertyRef = PropertyRef(
        "public_url",
        extra_index=True,
        description="Public web URL reported by Notion.",
    )
    is_public: PropertyRef = PropertyRef(
        "is_public",
        description="Whether Notion reports that the page is published to the web.",
    )
    created_time: PropertyRef = PropertyRef(
        "created_time",
        description="Timestamp when the page was created.",
    )
    last_edited_time: PropertyRef = PropertyRef(
        "last_edited_time",
        description="Timestamp when the page was last edited.",
    )
    in_trash: PropertyRef = PropertyRef(
        "in_trash",
        description="Whether the page is in the Notion trash.",
    )
    is_locked: PropertyRef = PropertyRef(
        "is_locked",
        description="Whether the page is locked from editing in Notion.",
    )
    parent_type: PropertyRef = PropertyRef(
        "parent_type",
        description="Type of the page's immediate Notion parent.",
    )
    parent_notion_id: PropertyRef = PropertyRef(
        "parent_notion_id",
        description="Notion UUID of the immediate parent when it has one.",
    )
    created_by_notion_user_id: PropertyRef = PropertyRef(
        "created_by_notion_user_id",
        description="Notion user UUID of the page creator.",
    )


@dataclass(frozen=True)
class NotionWorkspaceToPageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NotionWorkspaceToPageRel(CartographyRelSchema):
    """A Notion workspace contains a public page observed by the connection."""

    target_node_label: str = "NotionWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NotionWorkspaceToPageRelProperties = (
        NotionWorkspaceToPageRelProperties()
    )


@dataclass(frozen=True)
class NotionPageToCreatorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NotionPageToCreatorRel(CartographyRelSchema):
    """A public Notion page was created by a workspace user."""

    target_node_label: str = "NotionUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: NotionPageToCreatorRelProperties = NotionPageToCreatorRelProperties()


@dataclass(frozen=True)
class NotionPageSchema(CartographyNodeSchema):
    """A connection-visible Notion page observed as published to the web."""

    label: str = "NotionPage"
    properties: NotionPageNodeProperties = NotionPageNodeProperties()
    sub_resource_relationship: NotionWorkspaceToPageRel = NotionWorkspaceToPageRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [NotionPageToCreatorRel()],
    )
