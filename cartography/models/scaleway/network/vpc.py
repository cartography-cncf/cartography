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
class ScalewayVpcProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="VPC unique ID.")
    name: PropertyRef = PropertyRef("name", description="VPC name.")
    region: PropertyRef = PropertyRef("region", description="Region the VPC lives in.")
    tags: PropertyRef = PropertyRef("tags", description="Tags associated with the VPC.")
    is_default: PropertyRef = PropertyRef(
        "is_default", description="True if it is the default VPC of the Project."
    )
    private_network_count: PropertyRef = PropertyRef(
        "private_network_count", description="Number of Private Networks in the VPC."
    )
    routing_enabled: PropertyRef = PropertyRef(
        "routing_enabled",
        description="True if routing between Private Networks is enabled.",
    )
    custom_routes_propagation_enabled: PropertyRef = PropertyRef(
        "custom_routes_propagation_enabled",
        description="True if custom routes are propagated.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="VPC creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="VPC last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayVpcToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayVpc)
class ScalewayVpcToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayVpc` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayVpcToProjectRelProperties = ScalewayVpcToProjectRelProperties()


@dataclass(frozen=True)
class ScalewayVpcSchema(CartographyNodeSchema):
    """A VPC (Virtual Private Cloud) is a regional, isolated network that groups Private
    Networks.
    """

    label: str = "ScalewayVpc"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["VirtualNetwork"])
    properties: ScalewayVpcProperties = ScalewayVpcProperties()
    sub_resource_relationship: ScalewayVpcToProjectRel = ScalewayVpcToProjectRel()
