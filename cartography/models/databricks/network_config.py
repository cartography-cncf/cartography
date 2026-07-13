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
class DatabricksNetworkConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    network_id: PropertyRef = PropertyRef("network_id", extra_index=True)
    network_name: PropertyRef = PropertyRef("network_name", extra_index=True)
    vpc_id: PropertyRef = PropertyRef("vpc_id", extra_index=True)
    subnet_ids: PropertyRef = PropertyRef("subnet_ids")
    security_group_ids: PropertyRef = PropertyRef("security_group_ids")
    vpc_status: PropertyRef = PropertyRef("vpc_status")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksNetworkConfigToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksNetworkConfig)
class DatabricksNetworkConfigToAccountRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksNetworkConfigToAccountRelProperties = (
        DatabricksNetworkConfigToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksNetworkConfigToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksNetworkConfig)-[:USES_VPC]->(:AWSVpc)
class DatabricksNetworkConfigToVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vpc_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_VPC"
    properties: DatabricksNetworkConfigToVpcRelProperties = (
        DatabricksNetworkConfigToVpcRelProperties()
    )


@dataclass(frozen=True)
class DatabricksNetworkConfigToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksNetworkConfig)-[:USES_SUBNET]->(:AWSEC2Subnet)
class DatabricksNetworkConfigToSubnetRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subnet_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SUBNET"
    properties: DatabricksNetworkConfigToSubnetRelProperties = (
        DatabricksNetworkConfigToSubnetRelProperties()
    )


@dataclass(frozen=True)
class DatabricksNetworkConfigToSecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksNetworkConfig)-[:USES_SECURITY_GROUP]->(:AWSEC2SecurityGroup)
class DatabricksNetworkConfigToSecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("security_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECURITY_GROUP"
    properties: DatabricksNetworkConfigToSecurityGroupRelProperties = (
        DatabricksNetworkConfigToSecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class DatabricksNetworkConfigSchema(CartographyNodeSchema):
    label: str = "DatabricksNetworkConfig"
    properties: DatabricksNetworkConfigNodeProperties = (
        DatabricksNetworkConfigNodeProperties()
    )
    sub_resource_relationship: DatabricksNetworkConfigToAccountRel = (
        DatabricksNetworkConfigToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksNetworkConfigToVpcRel(),
            DatabricksNetworkConfigToSubnetRel(),
            DatabricksNetworkConfigToSecurityGroupRel(),
        ],
    )
