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
    id: PropertyRef = PropertyRef("partial_uri")
    partial_uri: PropertyRef = PropertyRef("partial_uri")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    self_link: PropertyRef = PropertyRef("self_link")
    project_id: PropertyRef = PropertyRef("project_id")
    zone: PropertyRef = PropertyRef("zone")
    region: PropertyRef = PropertyRef("region")
    description: PropertyRef = PropertyRef("description")
    network: PropertyRef = PropertyRef("network_partial_uri")
    subnetwork: PropertyRef = PropertyRef("subnetwork_partial_uri")
    size: PropertyRef = PropertyRef("size")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")


@dataclass(frozen=True)
class GCPInstanceGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
