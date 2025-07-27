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
class AirbyteConnectionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("connectionId")
    name: PropertyRef = PropertyRef("name")
    namespace_format: PropertyRef = PropertyRef("namespaceFormat")
    prefix: PropertyRef = PropertyRef("prefix")
    status: PropertyRef = PropertyRef("status")
    data_residency: PropertyRef = PropertyRef("dataResidency")
    non_breaking_schema_updates_behavior: PropertyRef = PropertyRef(
        "nonBreakingSchemaUpdatesBehavior"
    )
    namespace_definition: PropertyRef = PropertyRef("namespaceDefinition")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AirbyteConnectionToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteConnection)
class AirbyteConnectionToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteConnectionToOrganizationRelProperties = (
        AirbyteConnectionToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteConnectionToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteWorkspace)-[:CONTAINS]->(:AirbyteConnection)
class AirbyteConnectionToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "AirbyteWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AirbyteConnectionToWorkspaceRelProperties = (
        AirbyteConnectionToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AirbyteConnectionToSourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteSource)<-[:SYNC_FROM]-(:AirbyteConnection)
class AirbyteConnectionToSourceRel(CartographyRelSchema):
    target_node_label: str = "AirbyteSource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("sourceId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SYNC_FROM"
    properties: AirbyteConnectionToSourceRelProperties = (
        AirbyteConnectionToSourceRelProperties()
    )


@dataclass(frozen=True)
class AirbyteConnectionToDestinationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteDestination)<-[:SYNC_TO]-(:AirbyteConnection)
class AirbyteConnectionToDestinationRel(CartographyRelSchema):
    target_node_label: str = "AirbyteDestination"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("destinationId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SYNC_TO"
    properties: AirbyteConnectionToDestinationRelProperties = (
        AirbyteConnectionToDestinationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteConnectionToTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteTag)<-[:TAGGED]-(:AirbyteConnection)
class AirbyteConnectionToTagRel(CartographyRelSchema):
    target_node_label: str = "AirbyteTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tags_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TAGGED"
    properties: AirbyteConnectionToTagRelProperties = (
        AirbyteConnectionToTagRelProperties()
    )


@dataclass(frozen=True)
class AirbyteConnectionSchema(CartographyNodeSchema):
    label: str = "AirbyteConnection"
    properties: AirbyteConnectionNodeProperties = AirbyteConnectionNodeProperties()
    sub_resource_relationship: AirbyteConnectionToOrganizationRel = (
        AirbyteConnectionToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AirbyteConnectionToWorkspaceRel(),
            AirbyteConnectionToSourceRel(),
            AirbyteConnectionToDestinationRel(),
            AirbyteConnectionToTagRel(),
        ]
    )
