from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayAppleSiliconServerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the server.")
    name: PropertyRef = PropertyRef("name", description="Name of the server.")
    type: PropertyRef = PropertyRef(
        "type_", description="Commercial type of the server."
    )
    tags: PropertyRef = PropertyRef("tags", description="Tags attached to the server.")
    status: PropertyRef = PropertyRef("status", description="Status of the server.")
    ip: PropertyRef = PropertyRef("ip", description="Public IP address of the server.")
    vpc_status: PropertyRef = PropertyRef(
        "vpc_status", description="Private network status of the server."
    )
    public_bandwidth_bps: PropertyRef = PropertyRef(
        "public_bandwidth_bps", description="Public bandwidth in bits per second."
    )
    deletion_scheduled: PropertyRef = PropertyRef(
        "deletion_scheduled", description="Whether deletion is scheduled."
    )
    delivered: PropertyRef = PropertyRef(
        "delivered", description="Whether the server has been delivered."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone in which the server is located."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Date and time of server creation."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Date and time of last server update."
    )
    deletable_at: PropertyRef = PropertyRef(
        "deletable_at", description="Date and time the server can be deleted."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayAppleSiliconServerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayAppleSiliconServer)
class ScalewayAppleSiliconServerToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayAppleSiliconServer` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayAppleSiliconServerToProjectRelProperties = (
        ScalewayAppleSiliconServerToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayAppleSiliconServerSchema(CartographyNodeSchema):
    """Represents an Apple silicon (Mac mini) server in Scaleway."""

    label: str = "ScalewayAppleSiliconServer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: ScalewayAppleSiliconServerProperties = (
        ScalewayAppleSiliconServerProperties()
    )
    sub_resource_relationship: ScalewayAppleSiliconServerToProjectRel = (
        ScalewayAppleSiliconServerToProjectRel()
    )
