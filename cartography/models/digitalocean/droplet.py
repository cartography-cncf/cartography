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
class DODropletNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    locked: PropertyRef = PropertyRef("locked")
    status: PropertyRef = PropertyRef("status")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    image: PropertyRef = PropertyRef("image")
    size: PropertyRef = PropertyRef("size")
    kernel: PropertyRef = PropertyRef("kernel")
    tags: PropertyRef = PropertyRef("tags")
    volumes: PropertyRef = PropertyRef("volumes")
    vpc_uuid: PropertyRef = PropertyRef("vpc_uuid")
    ip_address: PropertyRef = PropertyRef("ip_address")
    private_ip_address: PropertyRef = PropertyRef("private_ip_address")
    ip_v6_address: PropertyRef = PropertyRef("ip_v6_address")
    account_id: PropertyRef = PropertyRef("ACCOUNT_ID", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef("PROJECT_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class DODropletToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DOProject)<-[:RESOURCE]-(:DODroplet)
class DODropletToAccountRel(CartographyRelSchema):
    target_node_label: str = "DOProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: DODropletToAccountRelProperties = DODropletToAccountRelProperties()


@dataclass(frozen=True)
class DODropletSchema(CartographyNodeSchema):
    label: str = "DODroplet"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: DODropletNodeProperties = DODropletNodeProperties()
    sub_resource_relationship: DODropletToAccountRel = DODropletToAccountRel()
