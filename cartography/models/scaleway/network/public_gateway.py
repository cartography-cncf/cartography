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
class ScalewayPublicGatewayProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Gateway UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Gateway name."
    )
    type: PropertyRef = PropertyRef(
        "type_", description="Commercial gateway type (for example, `VPC-GW-S`)."
    )
    bandwidth: PropertyRef = PropertyRef(
        "bandwidth", description="Gateway bandwidth in Mbps."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Gateway status (`running`, `stopped`, ...)."
    )
    tags: PropertyRef = PropertyRef("tags", description="Gateway tags.")
    # Public egress IP of the NAT gateway (flattened from the ipv4 object).
    ipv4_address: PropertyRef = PropertyRef(
        "ipv4_address", extra_index=True, description="Public egress IP of the gateway."
    )
    # SSH bastion exposure signals.
    bastion_enabled: PropertyRef = PropertyRef(
        "bastion_enabled", description="True if the SSH bastion is enabled."
    )
    bastion_port: PropertyRef = PropertyRef(
        "bastion_port", description="Port the SSH bastion listens on."
    )
    bastion_allowed_ips: PropertyRef = PropertyRef(
        "bastion_allowed_ips",
        description="CIDRs allowed to reach the bastion, if restricted.",
    )
    smtp_enabled: PropertyRef = PropertyRef(
        "smtp_enabled", description="True if outbound SMTP is allowed."
    )
    is_legacy: PropertyRef = PropertyRef(
        "is_legacy", description="True if this is a legacy (v1) gateway."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Gateway software version."
    )
    zone: PropertyRef = PropertyRef("zone", description="Zone the gateway lives in.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayPublicGatewayToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayPublicGateway)
class ScalewayPublicGatewayToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayPublicGateway` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayPublicGatewayToProjectRelProperties = (
        ScalewayPublicGatewayToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPublicGatewayToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayPublicGateway)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
# Represents the NAT / egress path: instances on the private network reach the
# internet through this gateway.
class ScalewayPublicGatewayToPrivateNetworkRel(CartographyRelSchema):
    """Connects `ScalewayPublicGateway` to `ScalewayPrivateNetwork` through `ATTACHED_TO`."""

    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayPublicGatewayToPrivateNetworkRelProperties = (
        ScalewayPublicGatewayToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPublicGatewaySchema(CartographyNodeSchema):
    """Represents a Scaleway Public Gateway: a managed NAT gateway providing internet
    egress (and optional SSH bastion) to instances on attached private networks.
    """

    label: str = "ScalewayPublicGateway"
    properties: ScalewayPublicGatewayProperties = ScalewayPublicGatewayProperties()
    sub_resource_relationship: ScalewayPublicGatewayToProjectRel = (
        ScalewayPublicGatewayToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayPublicGatewayToPrivateNetworkRel(),
        ]
    )
