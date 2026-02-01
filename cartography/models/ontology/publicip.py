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


# =============================================================================
# RESERVED_BY relations - Link PublicIP to provider-specific IP resources
# =============================================================================


# (:PublicIP)-[:RESERVED_BY]->(:ElasticIPAddress)
@dataclass(frozen=True)
class PublicIPToElasticIPAddressRel(CartographyRelSchema):
    target_node_label: str = "ElasticIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"public_ip": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESERVED_BY"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


# (:PublicIP)-[:RESERVED_BY]->(:AzurePublicIPAddress)
@dataclass(frozen=True)
class PublicIPToAzurePublicIPAddressRel(CartographyRelSchema):
    target_node_label: str = "AzurePublicIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ip_address": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESERVED_BY"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


# (:PublicIP)-[:RESERVED_BY]->(:ScalewayFlexibleIp)
@dataclass(frozen=True)
class PublicIPToScalewayFlexibleIpRel(CartographyRelSchema):
    target_node_label: str = "ScalewayFlexibleIp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"address": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESERVED_BY"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


# (:PublicIP)-[:RESERVED_BY]->(:GCPNicAccessConfig)
@dataclass(frozen=True)
class PublicIPToGCPNicAccessConfigRel(CartographyRelSchema):
    target_node_label: str = "GCPNicAccessConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"public_ip": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESERVED_BY"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


# =============================================================================
# POINTS_TO relations - Link PublicIP to ontology semantic labels
# These use the standardized _ont_* fields from the ontology mappings
# =============================================================================


# (:PublicIP)-[:POINTS_TO]->(:ComputeInstance)
@dataclass(frozen=True)
class PublicIPToComputeInstanceRel(CartographyRelSchema):
    target_node_label: str = "ComputeInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_public_ip_address": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "POINTS_TO"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


# (:PublicIP)-[:POINTS_TO]->(:LoadBalancer)
@dataclass(frozen=True)
class PublicIPToLoadBalancerRel(CartographyRelSchema):
    target_node_label: str = "LoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_ip_address": PropertyRef("ip_address")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "POINTS_TO"
    properties: PublicIPToNodeRelProperties = PublicIPToNodeRelProperties()


@dataclass(frozen=True)
class PublicIPSchema(CartographyNodeSchema):
    label: str = "PublicIP"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: PublicIPNodeProperties = PublicIPNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            # RESERVED_BY - Provider-specific IP resources
            PublicIPToElasticIPAddressRel(),
            PublicIPToAzurePublicIPAddressRel(),
            PublicIPToScalewayFlexibleIpRel(),
            PublicIPToGCPNicAccessConfigRel(),
            # POINTS_TO - Ontology semantic labels
            PublicIPToComputeInstanceRel(),
            PublicIPToLoadBalancerRel(),
        ],
    )
