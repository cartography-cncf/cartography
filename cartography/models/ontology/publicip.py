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
class PublicIPNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ip_address")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ip_address: PropertyRef = PropertyRef("ip_address", extra_index=True)
    ip_version: PropertyRef = PropertyRef("ip_version")


@dataclass(frozen=True)
class PublicIPToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:PublicIP)-[:RESERVED_BY]->(:ElasticIPAddress)
class PublicIPToElasticIPAddressRel(CartographyRelSchema):
    target_node_label: str = "ElasticIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"public_ip": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESERVED_BY"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


# (:PublicIP)-[:RESERVED_BY]->(:AzurePublicIPAddress)
class PublicIPToAzurePublicIPAddressRel(CartographyRelSchema):
    target_node_label: str = "AzurePublicIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ip_address": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESERVED_BY"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


# (:PublicIP)-[:RESERVED_BY]->(:ScalewayFlexibleIp)
class PublicIPToScalewayFlexibleIpRel(CartographyRelSchema):
    target_node_label: str = "ScalewayFlexibleIp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"address": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESERVED_BY"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


# (:PublicIP)-[:RESERVED_BY]->(:GCPNicAccessConfig)
class PublicIPToGCPNicAccessConfigRel(CartographyRelSchema):
    target_node_label: str = "GCPNicAccessConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"public_ip": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESERVED_BY"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


@dataclass(frozen=True)
class PublicIPSchema(CartographyNodeSchema):
    label: str = "PublicIP"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: PublicIPNodeProperties = PublicIPNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            PublicIPToElasticIPAddressRel(),
            PublicIPToAzurePublicIPAddressRel(),
            PublicIPToScalewayFlexibleIpRel(),
            PublicIPToGCPNicAccessConfigRel(),
            PublicIPToEC2PrivateIpRel(),
            PublicIPToEC2InstanceRel(),
        ],
    )
