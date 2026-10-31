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
class ScalewayIotHubProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Hub unique ID.")
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Hub name.")
    status: PropertyRef = PropertyRef(
        "status", description="Hub status (`ready`, `error`, `disabled`, ...)."
    )
    product_plan: PropertyRef = PropertyRef(
        "product_plan",
        description="Hub plan (`plan_shared`, `plan_dedicated`, `plan_ha`).",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the hub is enabled."
    )
    device_count: PropertyRef = PropertyRef(
        "device_count", description="Number of devices registered on this hub."
    )
    connected_device_count: PropertyRef = PropertyRef(
        "connected_device_count",
        description="Number of devices currently connected to this hub.",
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint", extra_index=True, description="MQTT endpoint for this hub."
    )
    disable_events: PropertyRef = PropertyRef(
        "disable_events", description="Whether hub events are disabled."
    )
    enable_device_auto_provisioning: PropertyRef = PropertyRef(
        "enable_device_auto_provisioning",
        description="Whether devices can auto-provision themselves on this hub.",
    )
    has_custom_ca: PropertyRef = PropertyRef(
        "has_custom_ca",
        description="Whether the hub has a custom certificate authority configured.",
    )
    region: PropertyRef = PropertyRef("region", description="Region the hub lives in.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Hub creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Hub last update date."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayIotHubToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayIotHub)
class ScalewayIotHubToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayIotHub` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayIotHubToProjectRelProperties = (
        ScalewayIotHubToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayIotHubSchema(CartographyNodeSchema):
    """Represents a Scaleway IoT Hub (MQTT broker)."""

    label: str = "ScalewayIotHub"
    properties: ScalewayIotHubProperties = ScalewayIotHubProperties()
    sub_resource_relationship: ScalewayIotHubToProjectRel = ScalewayIotHubToProjectRel()


@dataclass(frozen=True)
class ScalewayIotDeviceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Device unique ID."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Device name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Device description."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Device status (`enabled`, `disabled`, `error`, ...)."
    )
    is_connected: PropertyRef = PropertyRef(
        "is_connected", description="Whether the device is currently connected."
    )
    allow_insecure: PropertyRef = PropertyRef(
        "allow_insecure",
        description="Whether the device can connect without a certificate.",
    )
    allow_multiple_connections: PropertyRef = PropertyRef(
        "allow_multiple_connections",
        description="Whether multiple simultaneous connections are allowed for this device.",
    )
    has_custom_certificate: PropertyRef = PropertyRef(
        "has_custom_certificate",
        description="Whether the device has a custom certificate configured.",
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the device lives in."
    )
    last_activity_at: PropertyRef = PropertyRef(
        "last_activity_at", description="Time of the device's last activity."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Device creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Device last update date."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayIotDeviceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayIotDevice)
class ScalewayIotDeviceToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayIotDevice` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayIotDeviceToProjectRelProperties = (
        ScalewayIotDeviceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayIotDeviceToHubRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayIotHub)-[:HAS]->(:ScalewayIotDevice)
class ScalewayIotDeviceToHubRel(CartographyRelSchema):
    """Connects `ScalewayIotHub` to `ScalewayIotDevice` through `HAS`."""

    target_node_label: str = "ScalewayIotHub"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("hub_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayIotDeviceToHubRelProperties = (
        ScalewayIotDeviceToHubRelProperties()
    )


@dataclass(frozen=True)
class ScalewayIotDeviceSchema(CartographyNodeSchema):
    """A device registered on a Scaleway IoT Hub."""

    label: str = "ScalewayIotDevice"
    properties: ScalewayIotDeviceProperties = ScalewayIotDeviceProperties()
    sub_resource_relationship: ScalewayIotDeviceToProjectRel = (
        ScalewayIotDeviceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ScalewayIotDeviceToHubRel()],
    )
