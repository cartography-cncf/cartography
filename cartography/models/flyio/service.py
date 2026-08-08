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
class FlyMachineServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Synthesized `<machine_id>/<protocol>/<internal_port>` key."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    protocol: PropertyRef = PropertyRef("protocol", description="Service protocol.")
    internal_port: PropertyRef = PropertyRef(
        "internal_port", description="Internal port exposed by the Machine."
    )
    autostop: PropertyRef = PropertyRef(
        "autostop", description="Whether autostop is enabled."
    )
    autostart: PropertyRef = PropertyRef(
        "autostart", description="Whether autostart is enabled."
    )
    min_machines_running: PropertyRef = PropertyRef(
        "min_machines_running",
        description="Minimum number of Machines to keep running.",
    )
    force_instance_key: PropertyRef = PropertyRef(
        "force_instance_key", description="Force instance key setting."
    )
    machine_id: PropertyRef = PropertyRef(
        "machine_id", extra_index=True, description="Fly Machine ID."
    )
    app_id: PropertyRef = PropertyRef(
        "APP_ID", set_in_kwargs=True, description="Fly app ID."
    )


@dataclass(frozen=True)
class FlyMachineServiceToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyMachineService)
class FlyMachineServiceToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyMachineService` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyMachineServiceToAppRelProperties = (
        FlyMachineServiceToAppRelProperties()
    )


@dataclass(frozen=True)
class FlyMachineToServiceExposeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyMachine)-[:EXPOSE]->(:FlyMachineService)
class FlyMachineToServiceExposeRel(CartographyRelSchema):
    """Connects `FlyMachine` to the service it exposes."""

    target_node_label: str = "FlyMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("machine_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "EXPOSE"
    properties: FlyMachineToServiceExposeRelProperties = (
        FlyMachineToServiceExposeRelProperties()
    )


@dataclass(frozen=True)
class FlyMachineServiceSchema(CartographyNodeSchema):
    """Represents a service exposed from a Fly Machine config."""

    label: str = "FlyMachineService"
    properties: FlyMachineServiceNodeProperties = FlyMachineServiceNodeProperties()
    sub_resource_relationship: FlyMachineServiceToAppRel = FlyMachineServiceToAppRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            FlyMachineToServiceExposeRel(),
        ]
    )


@dataclass(frozen=True)
class FlyMachineServicePortNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthesized `<machine_id>/<protocol>/<internal_port>/<port>` key.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    port: PropertyRef = PropertyRef("port", description="Public port.")
    handlers: PropertyRef = PropertyRef(
        "handlers", description="Fly.io handlers applied to the public port."
    )
    force_https: PropertyRef = PropertyRef(
        "force_https", description="Whether HTTP traffic is forced to HTTPS."
    )
    service_id: PropertyRef = PropertyRef(
        "service_id", extra_index=True, description="Fly Machine Service ID."
    )
    app_id: PropertyRef = PropertyRef(
        "APP_ID", set_in_kwargs=True, description="Fly app ID."
    )


@dataclass(frozen=True)
class FlyMachineServicePortToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyMachineServicePort)
class FlyMachineServicePortToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyMachineServicePort` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyMachineServicePortToAppRelProperties = (
        FlyMachineServicePortToAppRelProperties()
    )


@dataclass(frozen=True)
class FlyMachineServiceToPortExposeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyMachineService)-[:EXPOSE]->(:FlyMachineServicePort)
class FlyMachineServiceToPortExposeRel(CartographyRelSchema):
    """Connects `FlyMachineService` to the public port it exposes."""

    target_node_label: str = "FlyMachineService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "EXPOSE"
    properties: FlyMachineServiceToPortExposeRelProperties = (
        FlyMachineServiceToPortExposeRelProperties()
    )


@dataclass(frozen=True)
class FlyMachineServicePortSchema(CartographyNodeSchema):
    """Represents a public port exposed by a Fly Machine service."""

    label: str = "FlyMachineServicePort"
    properties: FlyMachineServicePortNodeProperties = (
        FlyMachineServicePortNodeProperties()
    )
    sub_resource_relationship: FlyMachineServicePortToAppRel = (
        FlyMachineServicePortToAppRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            FlyMachineServiceToPortExposeRel(),
        ]
    )
