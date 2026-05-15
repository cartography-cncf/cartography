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
class GCPNicAccessConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("access_config_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    name: PropertyRef = PropertyRef("name")
    public_ip: PropertyRef = PropertyRef("natIP")
    set_public_ptr: PropertyRef = PropertyRef("setPublicPtr")
    public_ptr_domain_name: PropertyRef = PropertyRef("publicPtrDomainName")
    network_tier: PropertyRef = PropertyRef("networkTier")


@dataclass(frozen=True)
class GCPNicAccessConfigToNicRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNicAccessConfigToNicRel(CartographyRelSchema):
    target_node_label: str = "GCPNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("nic_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPNicAccessConfigToNicRelProperties = (
        GCPNicAccessConfigToNicRelProperties()
    )


@dataclass(frozen=True)
class GCPNicAccessConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNicAccessConfigToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPNicAccessConfigToProjectRelProperties = (
        GCPNicAccessConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPNicAccessConfigSchema(CartographyNodeSchema):
    label: str = "GCPNicAccessConfig"
    properties: GCPNicAccessConfigNodeProperties = GCPNicAccessConfigNodeProperties()
    sub_resource_relationship: GCPNicAccessConfigToProjectRel = (
        GCPNicAccessConfigToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPNicAccessConfigToNicRel(),
        ]
    )
