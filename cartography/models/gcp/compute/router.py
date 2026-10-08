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
class GCPRouterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri", description="Stable identifier for this Cloud Router."
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the Cloud Router."
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the Cloud Router."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this Cloud Router belongs to."
    )
    region: PropertyRef = PropertyRef(
        "region", description="The region where this Cloud Router is configured."
    )
    network: PropertyRef = PropertyRef(
        "network_partial_uri",
        description="A partial resource URI of the VPC network this Cloud Router belongs to.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of this Cloud Router."
    )


@dataclass(frozen=True)
class GCPRouterToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPRouterToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPRouterToProjectRelProperties = GCPRouterToProjectRelProperties()


@dataclass(frozen=True)
class GCPRouterToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPRouterToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("network_partial_uri"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: GCPRouterToVpcRelProperties = GCPRouterToVpcRelProperties()


@dataclass(frozen=True)
class GCPRouterSchema(CartographyNodeSchema):
    """Representation of a GCP [Cloud Router](https://cloud.google.com/compute/docs/reference/rest/v1/routers)."""

    label: str = "GCPRouter"
    properties: GCPRouterNodeProperties = GCPRouterNodeProperties()
    sub_resource_relationship: GCPRouterToProjectRel = GCPRouterToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPRouterToVpcRel(),
        ],
    )
