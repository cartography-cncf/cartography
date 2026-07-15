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
class AirbyteStreamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("streamId", description="Stream identifier.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Stream name.")
    sync_mode: PropertyRef = PropertyRef(
        "syncMode", description="Synchronization mode for the stream."
    )
    cursor_field: PropertyRef = PropertyRef(
        "cursorField", description="Field used as the synchronization cursor."
    )
    primary_key: PropertyRef = PropertyRef(
        "primaryKey", description="Primary key fields for the stream."
    )
    include_files: PropertyRef = PropertyRef(
        "includeFiles", description="Whether blob synchronization includes raw files."
    )
    selected_fields: PropertyRef = PropertyRef(
        "selectedFields", description="Fields selected for synchronization."
    )
    mappers: PropertyRef = PropertyRef(
        "mappers", description="Custom mappers configured for the stream."
    )


@dataclass(frozen=True)
class AirbyteStreamToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteStream)
class AirbyteStreamToOrganizationRel(CartographyRelSchema):
    """Links an organization to a stream it owns."""

    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteStreamToOrganizationRelProperties = (
        AirbyteStreamToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteStreamToConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteConnection)-[:HAS]->(:AirbyteStream)
class AirbyteStreamToConnectionRel(CartographyRelSchema):
    """Links a connection to a stream it synchronizes."""

    target_node_label: str = "AirbyteConnection"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("connectionId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: AirbyteStreamToOrganizationRelProperties = (
        AirbyteStreamToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteStreamSchema(CartographyNodeSchema):
    """A data stream synchronized by an Airbyte connection."""

    label: str = "AirbyteStream"
    properties: AirbyteStreamNodeProperties = AirbyteStreamNodeProperties()
    sub_resource_relationship: AirbyteStreamToOrganizationRel = (
        AirbyteStreamToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AirbyteStreamToConnectionRel()]
    )
