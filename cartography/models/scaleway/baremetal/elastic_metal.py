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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    tags: PropertyRef = PropertyRef("tags")
    status: PropertyRef = PropertyRef("status")
    offer_id: PropertyRef = PropertyRef("offer_id")
    offer_name: PropertyRef = PropertyRef("offer_name")
    domain: PropertyRef = PropertyRef("domain")
    boot_type: PropertyRef = PropertyRef("boot_type")
    ping_status: PropertyRef = PropertyRef("ping_status")
    protected: PropertyRef = PropertyRef("protected")
    # Public IP addresses attached to the server. Persisted so exposure rules
    # can test for a public IP without a separate node.
    ips: PropertyRef = PropertyRef("ips")
    # First public IP, as a scalar, for the ComputeInstance ontology mapping.
    public_ip: PropertyRef = PropertyRef("public_ip")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayElasticMetalServerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayElasticMetalServer)
class ScalewayElasticMetalServerToProjectRel(CartographyRelSchema):
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
    label: str = "ScalewayElasticMetalServer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: ScalewayElasticMetalServerProperties = (
        ScalewayElasticMetalServerProperties()
    )
    sub_resource_relationship: ScalewayElasticMetalServerToProjectRel = (
        ScalewayElasticMetalServerToProjectRel()
    )
