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
class AirbyteDestinationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("destinationId")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("destinationType")
    config_host: PropertyRef = PropertyRef("configuration.host")
    config_port: PropertyRef = PropertyRef("configuration.port")
    config_name: PropertyRef = PropertyRef("configuration.name")
    config_region: PropertyRef = PropertyRef("configuration.region")
    config_endpoint: PropertyRef = PropertyRef("configuration.endpoint")
    config_account: PropertyRef = PropertyRef("configuration.account")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AirbyteDestinationToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteDestination)
class AirbyteDestinationToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteDestinationToOrganizationRelProperties = (
        AirbyteDestinationToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteDestinationToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteWorkspace)-[:CONTAINS]->(:AirbyteDestination)
class AirbyteDestinationToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "AirbyteWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AirbyteDestinationToWorkspaceRelProperties = (
        AirbyteDestinationToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AirbyteDestinationSchema(CartographyNodeSchema):
    label: str = "AirbyteDestination"
    properties: AirbyteDestinationNodeProperties = AirbyteDestinationNodeProperties()
    sub_resource_relationship: AirbyteDestinationToOrganizationRel = (
        AirbyteDestinationToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AirbyteDestinationToWorkspaceRel()]
    )
