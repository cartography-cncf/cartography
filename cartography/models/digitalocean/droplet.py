from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DODropletNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="DigitalOcean Droplet ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Droplet name.")
    locked: PropertyRef = PropertyRef(
        "locked",
        description="Whether user actions are blocked.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Droplet lifecycle status.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="DigitalOcean region slug.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Droplet creation timestamp.",
    )
    image: PropertyRef = PropertyRef("image", description="Base image slug.")
    size: PropertyRef = PropertyRef("size", description="Droplet size slug.")
    kernel: PropertyRef = PropertyRef(
        "kernel",
        description="Current kernel information.",
    )
    tags: PropertyRef = PropertyRef("tags", description="Tags assigned to the Droplet.")
    volumes: PropertyRef = PropertyRef(
        "volumes",
        description="Attached block-storage volume IDs.",
    )
    vpc_uuid: PropertyRef = PropertyRef(
        "vpc_uuid",
        description="UUID of the Droplet's VPC.",
    )
    ip_address: PropertyRef = PropertyRef(
        "ip_address",
        description="Public IPv4 address.",
    )
    private_ip_address: PropertyRef = PropertyRef(
        "private_ip_address",
        description="Private IPv4 address.",
    )
    ip_v6_address: PropertyRef = PropertyRef(
        "ip_v6_address",
        description="Public IPv6 address.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        description="ID of the owning account.",
    )
    project_id: PropertyRef = PropertyRef(
        "PROJECT_ID",
        set_in_kwargs=True,
        description="ID of the containing project.",
    )


@dataclass(frozen=True)
class DODropletToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DOProject)-[:RESOURCE]->(:DODroplet)
class DODropletToAccountRel(CartographyRelSchema):
    """The project contains the Droplet."""

    target_node_label: str = "DOProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DODropletToAccountRelProperties = DODropletToAccountRelProperties()


@dataclass(frozen=True)
# (:DOProject)<-[:RESOURCE]-(:DODroplet) - Backwards compatibility
class DODropletToProjectDeprecatedRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a Droplet to its project."""

    target_node_label: str = "DOProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: DODropletToAccountRelProperties = DODropletToAccountRelProperties()


@dataclass(frozen=True)
class DODropletSchema(CartographyNodeSchema):
    """A compute instance in a DigitalOcean project."""

    label: str = "DODroplet"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: DODropletNodeProperties = DODropletNodeProperties()
    sub_resource_relationship: DODropletToAccountRel = DODropletToAccountRel()
    # DEPRECATED: for backward compatibility, will be removed in v1.0.0
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[DODropletToProjectDeprecatedRel()],
    )
