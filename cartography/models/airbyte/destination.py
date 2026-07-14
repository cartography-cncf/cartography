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
    id: PropertyRef = PropertyRef("destinationId", description="Destination UUID.")
    name: PropertyRef = PropertyRef("name", description="Destination name.")
    type: PropertyRef = PropertyRef(
        "destinationType", description="Destination connector type."
    )
    config_host: PropertyRef = PropertyRef(
        "configuration.host", description="Configured destination host."
    )
    config_port: PropertyRef = PropertyRef(
        "configuration.port", description="Configured destination port."
    )
    config_name: PropertyRef = PropertyRef(
        "configuration.name", description="Configured destination resource name."
    )
    config_region: PropertyRef = PropertyRef(
        "configuration.region", description="Configured destination region."
    )
    config_endpoint: PropertyRef = PropertyRef(
        "configuration.endpoint", description="Configured destination endpoint."
    )
    config_account: PropertyRef = PropertyRef(
        "configuration.account", description="Configured destination account."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class AirbyteDestinationToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteDestination)
class AirbyteDestinationToOrganizationRel(CartographyRelSchema):
    """Links an organization to a destination it owns."""

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
    """Links a workspace to a destination it contains."""

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
    """A data destination configured in Airbyte."""

    label: str = "AirbyteDestination"
    properties: AirbyteDestinationNodeProperties = AirbyteDestinationNodeProperties()
    sub_resource_relationship: AirbyteDestinationToOrganizationRel = (
        AirbyteDestinationToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AirbyteDestinationToWorkspaceRel()]
    )
