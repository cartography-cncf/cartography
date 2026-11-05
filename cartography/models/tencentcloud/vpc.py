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
from cartography.models.ontology.labels import VIRTUAL_NETWORK


@dataclass(frozen=True)
class TencentCloudVPCNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="VPC ID, e.g. `vpc-azd4dt1c`.")
    name: PropertyRef = PropertyRef("name", description="Name of the VPC.")
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Region the VPC is in."
    )
    cidr_block: PropertyRef = PropertyRef(
        "cidr_block", description="Primary IPv4 CIDR block of the VPC."
    )
    assistant_cidr_blocks: PropertyRef = PropertyRef(
        "assistant_cidr_blocks", description="Secondary IPv4 CIDR blocks of the VPC."
    )
    ipv6_cidr_block: PropertyRef = PropertyRef(
        "ipv6_cidr_block", description="IPv6 CIDR block of the VPC."
    )
    is_default: PropertyRef = PropertyRef(
        "is_default", description="`True` for the region's default VPC."
    )
    enable_multicast: PropertyRef = PropertyRef(
        "enable_multicast", description="`True` when multicast is enabled."
    )
    dns_servers: PropertyRef = PropertyRef(
        "dns_servers", description="DNS servers handed out by the VPC's DHCP options."
    )
    domain_name: PropertyRef = PropertyRef(
        "domain_name", description="DHCP domain name option."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags on the VPC, as `key:value` strings."
    )
    created_time: PropertyRef = PropertyRef(
        "created_time", description="Time the VPC was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudVPCToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudVPC)
class TencentCloudVPCToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its VPCs."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudVPCToAccountRelProperties = (
        TencentCloudVPCToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudVPCSchema(CartographyNodeSchema):
    """A Virtual Private Cloud: an isolated network in one region."""

    label: str = "TencentCloudVPC"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([VIRTUAL_NETWORK])
    properties: TencentCloudVPCNodeProperties = TencentCloudVPCNodeProperties()
    sub_resource_relationship: TencentCloudVPCToAccountRel = (
        TencentCloudVPCToAccountRel()
    )
