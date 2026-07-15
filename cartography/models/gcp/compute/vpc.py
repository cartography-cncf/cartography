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
class GCPVpcNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri",
        extra_index=True,
        description="The partial resource URI representing this VPC.  Has the form `projects/{project_name}/global/networks/{vpc name}`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    self_link: PropertyRef = PropertyRef(
        "self_link",
        description="The full resource URI representing this VPC. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the VPC."
    )
    project_id: PropertyRef = PropertyRef(
        "PROJECT_ID",
        set_in_kwargs=True,
        description="The project ID that this VPC belongs to.",
    )
    auto_create_subnetworks: PropertyRef = PropertyRef(
        "auto_create_subnetworks",
        description='When set to true, the VPC network is created in "auto" mode. When set to false, the VPC network is created in "custom" mode.  An auto mode VPC network starts with one subnet per region. Each subnet has a predetermined range as described in [Auto mode VPC network IP ranges](https://cloud.google.com/vpc/docs/vpc#ip-ranges).',
    )
    routing_config_routing_mode: PropertyRef = PropertyRef(
        "routing_config_routing_mode",
        description="VPC dynamic routing mode, either REGIONAL or GLOBAL.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="A description for the VPC."
    )


@dataclass(frozen=True)
class GCPVpcToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPVpcToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVpcToProjectRelProperties = GCPVpcToProjectRelProperties()


@dataclass(frozen=True)
class GCPVpcSchema(CartographyNodeSchema):
    """Representation of a GCP [VPC](https://cloud.google.com/compute/docs/reference/rest/v1/networks/).  In GCP documentation this is also known simply as a "Network" object."""

    label: str = "GCPVpc"
    properties: GCPVpcNodeProperties = GCPVpcNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["VirtualNetwork"])
    sub_resource_relationship: GCPVpcToProjectRel = GCPVpcToProjectRel()
