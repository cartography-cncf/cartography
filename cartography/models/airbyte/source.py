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
class AirbyteSourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("sourceId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("sourceType")
    config_host: PropertyRef = PropertyRef("configuration.host")
    config_port: PropertyRef = PropertyRef("configuration.port")
    config_name: PropertyRef = PropertyRef("configuration.name")
    config_region: PropertyRef = PropertyRef("configuration.region")
    config_endpoint: PropertyRef = PropertyRef("configuration.endpoint")
    config_account: PropertyRef = PropertyRef("configuration.account")


@dataclass(frozen=True)
class AirbyteSourceToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteSource)
class AirbyteSourceToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteSourceToOrganizationRelProperties = (
        AirbyteSourceToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteSourceToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteWorkspace)-[:CONTAINS]->(:AirbyteSource)
class AirbyteSourceToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "AirbyteWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AirbyteSourceToWorkspaceRelProperties = (
        AirbyteSourceToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AirbyteSourceSchema(CartographyNodeSchema):
    label: str = "AirbyteSource"
    properties: AirbyteSourceNodeProperties = AirbyteSourceNodeProperties()
    sub_resource_relationship: AirbyteSourceToOrganizationRel = (
        AirbyteSourceToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AirbyteSourceToWorkspaceRel()]
    )
