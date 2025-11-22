from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KonnectDPNodeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef("hostname")
    version: PropertyRef = PropertyRef("version")
    status: PropertyRef = PropertyRef("status")
    last_ping: PropertyRef = PropertyRef("last_ping")
    config_hash: PropertyRef = PropertyRef("config_hash")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class KonnectDPNodeToControlPlaneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KonnectDPNode)-[:RESOURCE]->(:KonnectControlPlane)
class KonnectDPNodeToControlPlaneRel(CartographyRelSchema):
    target_node_label: str = "KonnectControlPlane"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CONTROL_PLANE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: KonnectDPNodeToControlPlaneRelProperties = (
        KonnectDPNodeToControlPlaneRelProperties()
    )


@dataclass(frozen=True)
class KonnectDPNodeSchema(CartographyNodeSchema):
    label: str = "KonnectDPNode"
    properties: KonnectDPNodeNodeProperties = KonnectDPNodeNodeProperties()
    sub_resource_relationship: KonnectDPNodeToControlPlaneRel = (
        KonnectDPNodeToControlPlaneRel()
    )
