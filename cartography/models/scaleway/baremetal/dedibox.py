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
    id: PropertyRef = PropertyRef("id")
    hostname: PropertyRef = PropertyRef("hostname")
    datacenter_name: PropertyRef = PropertyRef("datacenter_name")
    offer_id: PropertyRef = PropertyRef("offer_id")
    offer_name: PropertyRef = PropertyRef("offer_name")
    status: PropertyRef = PropertyRef("status")
    # Public IP addresses across the server network interfaces. Persisted so
    # exposure rules can test for a public IP without a separate node.
    ips: PropertyRef = PropertyRef("ips")
    # First public IP, as a scalar, for the ComputeInstance ontology mapping.
    public_ip: PropertyRef = PropertyRef("public_ip")
    is_outsourced: PropertyRef = PropertyRef("is_outsourced")
    is_hds: PropertyRef = PropertyRef("is_hds")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    expired_at: PropertyRef = PropertyRef("expired_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayDediboxServerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayDediboxServer)
class ScalewayDediboxServerToProjectRel(CartographyRelSchema):
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
    label: str = "ScalewayDediboxServer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: ScalewayDediboxServerProperties = ScalewayDediboxServerProperties()
    sub_resource_relationship: ScalewayDediboxServerToProjectRel = (
        ScalewayDediboxServerToProjectRel()
    )
