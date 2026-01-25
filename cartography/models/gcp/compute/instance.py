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
class GCPInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("partial_uri")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    self_link: PropertyRef = PropertyRef("selfLink")
    instancename: PropertyRef = PropertyRef("name", extra_index=True)
    hostname: PropertyRef = PropertyRef("hostname")
    zone_name: PropertyRef = PropertyRef("zone_name")
    project_id: PropertyRef = PropertyRef("project_id")
    status: PropertyRef = PropertyRef("status")


@dataclass(frozen=True)
class GCPInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPInstanceToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPInstanceToProjectRelProperties = GCPInstanceToProjectRelProperties()


@dataclass(frozen=True)
class GCPInstanceSchema(CartographyNodeSchema):
    label: str = "GCPInstance"
    properties: GCPInstanceNodeProperties = GCPInstanceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Instance"])
    sub_resource_relationship: GCPInstanceToProjectRel = GCPInstanceToProjectRel()
