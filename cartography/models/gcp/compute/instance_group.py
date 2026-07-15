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
class GCPInstanceGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri", description="Stable identifier for this resource."
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name assigned to this resource."
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the resource."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this instance group belongs to."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="The zone of this instance group."
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="The region of this instance group (for regional instance groups).",
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of this instance group."
    )
    network: PropertyRef = PropertyRef(
        "network_partial_uri",
        description="The partial URI of the VPC network this instance group belongs to.",
    )
    subnetwork: PropertyRef = PropertyRef(
        "subnetwork_partial_uri",
        description="The partial URI of the subnet this instance group belongs to.",
    )
    size: PropertyRef = PropertyRef(
        "size", description="The number of instances in this instance group."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp", description="Creation timestamp of the resource."
    )


@dataclass(frozen=True)
class GCPInstanceGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPInstanceGroupToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPInstanceGroupToProjectRelProperties = (
        GCPInstanceGroupToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPInstanceGroupToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPInstanceGroupToInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("member_instance_partial_uris", one_to_many=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_MEMBER"
    properties: GCPInstanceGroupToInstanceRelProperties = (
        GCPInstanceGroupToInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPInstanceGroupSchema(CartographyNodeSchema):
    """Representation of a GCP [Instance Group](https://cloud.google.com/compute/docs/reference/rest/v1/instanceGroups). Instance groups are collections of VM instances that can be managed together and serve as backends for load balancing."""

    label: str = "GCPInstanceGroup"
    properties: GCPInstanceGroupNodeProperties = GCPInstanceGroupNodeProperties()
    sub_resource_relationship: GCPInstanceGroupToProjectRel = (
        GCPInstanceGroupToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPInstanceGroupToInstanceRel(),
        ],
    )
