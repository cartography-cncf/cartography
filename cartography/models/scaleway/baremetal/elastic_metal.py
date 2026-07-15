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
class ScalewayElasticMetalServerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the server.")
    name: PropertyRef = PropertyRef("name", description="Name of the server.")
    description: PropertyRef = PropertyRef(
        "description", description="Description of the server."
    )
    tags: PropertyRef = PropertyRef("tags", description="Tags attached to the server.")
    status: PropertyRef = PropertyRef("status", description="Status of the server.")
    offer_id: PropertyRef = PropertyRef(
        "offer_id", description="Offer ID of the server."
    )
    offer_name: PropertyRef = PropertyRef(
        "offer_name", description="Offer name of the server."
    )
    domain: PropertyRef = PropertyRef("domain", description="Domain of the server.")
    boot_type: PropertyRef = PropertyRef(
        "boot_type", description="Boot type of the server."
    )
    ping_status: PropertyRef = PropertyRef(
        "ping_status", description="Status of the server ping."
    )
    protected: PropertyRef = PropertyRef(
        "protected", description="If enabled, the server can not be deleted."
    )
    # Public IP addresses attached to the server. Persisted so exposure rules
    # can test for a public IP without a separate node.
    ips: PropertyRef = PropertyRef(
        "ips", description="Public IP addresses attached to the server."
    )
    # First public IP, as a scalar, for the ComputeInstance ontology mapping.
    public_ip: PropertyRef = PropertyRef(
        "public_ip", description="First public IP (scalar, for ontology)."
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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayElasticMetalServerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayElasticMetalServer)
class ScalewayElasticMetalServerToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayElasticMetalServer` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayElasticMetalServerToProjectRelProperties = (
        ScalewayElasticMetalServerToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayElasticMetalServerSchema(CartographyNodeSchema):
    """Represents an Elastic Metal (bare-metal) server in Scaleway."""

    label: str = "ScalewayElasticMetalServer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: ScalewayElasticMetalServerProperties = (
        ScalewayElasticMetalServerProperties()
    )
    sub_resource_relationship: ScalewayElasticMetalServerToProjectRel = (
        ScalewayElasticMetalServerToProjectRel()
    )
