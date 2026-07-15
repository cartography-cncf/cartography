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
class ScalewayDediboxServerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the server (stringified).")
    hostname: PropertyRef = PropertyRef(
        "hostname", description="Hostname of the server."
    )
    datacenter_name: PropertyRef = PropertyRef(
        "datacenter_name", description="Datacenter hosting the server."
    )
    offer_id: PropertyRef = PropertyRef(
        "offer_id", description="Offer ID of the server."
    )
    offer_name: PropertyRef = PropertyRef(
        "offer_name", description="Offer name of the server."
    )
    status: PropertyRef = PropertyRef("status", description="Status of the server.")
    # Public IP addresses across the server network interfaces. Persisted so
    # exposure rules can test for a public IP without a separate node.
    ips: PropertyRef = PropertyRef(
        "ips", description="Public IP addresses of the server."
    )
    # First public IP, as a scalar, for the ComputeInstance ontology mapping.
    public_ip: PropertyRef = PropertyRef(
        "public_ip", description="First public IP (scalar, for ontology)."
    )
    is_outsourced: PropertyRef = PropertyRef(
        "is_outsourced", description="Whether the server is outsourced."
    )
    is_hds: PropertyRef = PropertyRef(
        "is_hds", description="Whether the server is HDS certified."
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
    expired_at: PropertyRef = PropertyRef(
        "expired_at", description="Date and time the server expires."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayDediboxServerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayDediboxServer)
class ScalewayDediboxServerToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayDediboxServer` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayDediboxServerToProjectRelProperties = (
        ScalewayDediboxServerToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayDediboxServerSchema(CartographyNodeSchema):
    """Represents a Dedibox (dedicated) server in Scaleway."""

    label: str = "ScalewayDediboxServer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: ScalewayDediboxServerProperties = ScalewayDediboxServerProperties()
    sub_resource_relationship: ScalewayDediboxServerToProjectRel = (
        ScalewayDediboxServerToProjectRel()
    )
