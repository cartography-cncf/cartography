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
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks network configuration ID.",
    )
    network_id: PropertyRef = PropertyRef(
        "network_id",
        extra_index=True,
        description="Databricks network configuration ID.",
    )
    network_name: PropertyRef = PropertyRef(
        "network_name",
        extra_index=True,
        description="Network configuration name.",
    )
    vpc_id: PropertyRef = PropertyRef(
        "vpc_id",
        extra_index=True,
        description="ID of the customer-managed AWS VPC.",
    )
    subnet_ids: PropertyRef = PropertyRef(
        "subnet_ids",
        description="IDs of the AWS subnets used by the configuration.",
    )
    security_group_ids: PropertyRef = PropertyRef(
        "security_group_ids",
        description="IDs of the AWS security groups used by the configuration.",
    )
    vpc_status: PropertyRef = PropertyRef(
        "vpc_status",
        description="Validation status of the customer-managed VPC.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksNetworkConfigToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksNetworkConfig)
class DatabricksNetworkConfigToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

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
    """A Databricks network configuration uses an AWS VPC."""

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
    """A Databricks network configuration uses an AWS subnet."""

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
    """A Databricks network configuration uses an AWS security group."""

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
    """A Databricks customer-managed VPC network configuration."""

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
