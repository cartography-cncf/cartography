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
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class NotionGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Workspace-scoped Notion group ID.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    notion_group_id: PropertyRef = PropertyRef(
        "notion_group_id",
        extra_index=True,
        description="Notion group UUID returned by SCIM.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="SCIM group display name.",
    )
    scim_external_id: PropertyRef = PropertyRef(
        "scim_external_id",
        description="Identity provider group ID supplied through SCIM.",
    )


@dataclass(frozen=True)
class NotionWorkspaceToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NotionWorkspaceToGroupRel(CartographyRelSchema):
    """A Notion workspace contains a SCIM group."""

    target_node_label: str = "NotionWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NotionWorkspaceToGroupRelProperties = (
        NotionWorkspaceToGroupRelProperties()
    )


@dataclass(frozen=True)
class NotionUserToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NotionUserToGroupRel(CartographyRelSchema):
    """A Notion user is a member of a SCIM group."""

    target_node_label: str = "NotionUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: NotionUserToGroupRelProperties = NotionUserToGroupRelProperties()


@dataclass(frozen=True)
class NotionGroupSchema(CartographyNodeSchema):
    """A Notion SCIM group with the canonical UserGroup label."""

    label: str = "NotionGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
    properties: NotionGroupNodeProperties = NotionGroupNodeProperties()
    sub_resource_relationship: NotionWorkspaceToGroupRel = NotionWorkspaceToGroupRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [NotionUserToGroupRel()],
    )
